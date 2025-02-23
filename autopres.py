import base64
import os
import json
import time
from datetime import datetime
from typing import Optional, Dict, List, Union
import dotenv
from bs4 import BeautifulSoup
from pathlib import Path
import logging
import google.generativeai as genai
import requests
import urllib.request

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_DIR = "local_gens/image_suggestions"
BING_SEARCH_URL = "http://www.bing.com/images/search?q="
HEADERS = {
    'User-Agent': "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/43.0.2357.134 Safari/537.36"
}

def get_soup(url,header):
    #return BeautifulSoup(urllib2.urlopen(urllib2.Request(url,headers=header)),
    # 'html.parser')
    return BeautifulSoup(urllib.request.urlopen(
        urllib.request.Request(url,headers=header)),
        'html.parser')

def scrape_images(query, save_path, max_images=2):
    """Scrape images for a given query and save them in the specified path."""
    url = BING_SEARCH_URL + query.replace(" ", "+") + "&FORM=HDRSC2"
    soup = get_soup(url, HEADERS)

    actual_images = []
    for a in soup.find_all("a", {"class": "iusc"}):
        try:
            m_data = json.loads(a.get("m", "{}"))
            murl = m_data.get("murl")
            if murl:
                actual_images.append(murl)
                if len(actual_images) >= max_images:
                    break
        except json.JSONDecodeError:
            continue

    os.makedirs(save_path, exist_ok=True)

    for i, img_url in enumerate(actual_images):
        try:
            img_data = urllib.request.urlopen(img_url).read()
            file_path = os.path.join(save_path, f"image_{i+1}.jpg")
            with open(file_path, "wb") as f:
                f.write(img_data)
            print(f"Saved: {file_path}")
        except Exception as e:
            print(f"Failed to download {img_url}: {e}")

def process_html(html_file):
    """Extract sections and their image suggestions, then scrape images."""
    with open(html_file, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")

    for section in soup.find_all("div", id=True):
        section_id = section.get("id")
        image_suggestions = section.find("div", class_="image_suggestions")

        if image_suggestions:
            queries = [li.text.strip() for li in image_suggestions.find_all("li")]
            section_dir = os.path.join(BASE_DIR, section_id)
            
            for query in queries:
                query_dir = os.path.join(section_dir, query.replace(" ", "_"))
                scrape_images(query, query_dir)

def parse_html_to_json(html_file):
    """Parses an HTML file and returns a structured JSON dictionary."""
    with open(html_file, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")
    
    sections = {}
    
    for section in soup.find_all("div", id=True):
        section_id = section.get("id")
        section_title = section.find(["h1", "h2", "h3", "h4", "h5", "h6"])
        
        text_content = section.find("div", class_="section_text")
        suggestions = section.find("div", class_="suggestions")
        image_suggestions = section.find("div", class_="image_suggestions")
        
        sections[section_id] = {
            "title": section_title.text.strip() if section_title else "",
            "text": text_content.text.strip() if text_content else "",
            "suggestions": suggestions.text.strip() if suggestions else "",
            "image_suggestions": [li.text.strip() for li in image_suggestions.find_all("li")] if image_suggestions else []
        }
    
    return sections

class ScriptGenerator:
    """A class to generate reveal.js presentations using Google's Gemini API."""

    def __init__(self, save_dir: str = "./"):
        """
        Initialize the PresentationGenerator.

        Args:
            save_dir (str): Directory to save generated presentations
        """
        dotenv.load_dotenv()
        
        self.api_key = open("gem.api", "r").read()

        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-2.0-pro-exp-02-05')  # Or an appropriate model
        self.base_dir = Path(save_dir) / "scripts"
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.save_dir = Path(save_dir) / "local_gens"

        # Load system prompt template
        prompt_path = Path(__file__).parent / "Prompt_templates/intermediate_template.txt"
        with open(prompt_path, "r") as f:
            self.prompt_template = f.read()

    def _validate_html(self, html_content: str) -> bool:
        """
        Validate that the HTML content follows the required format.

        Args:
            html_content (str): HTML content to validate.

        Returns:
            bool: True if valid, False otherwise.
        """
        try:
            soup = BeautifulSoup(html_content, "html.parser")

            # Find all section divs
            sections = soup.find_all("div", id=True)  # Ensures each section has an ID
            if not sections:
                logger.error("No valid section divs found.")
                return False

            for section in sections:
                # Ensure each section has at least one header (h1, h2, or h3)
                if not section.find(["h1", "h2", "h3"]):
                    logger.error(f"Section {section.get('id')} is missing a header.")
                    return False

                # Ensure it contains a 'section_text' div
                if not section.find("div", class_="section_text"):
                    logger.error(f"Section {section.get('id')} is missing a 'section_text' div.")
                    return False

            return True

        except Exception as e:
            logger.error(f"HTML validation error: {e}")
            return False

    def _build_prompt(
        self, content: str, additional_context: Optional[Dict] = None
    ) -> str:
        """
        Build the prompt for the Gemini API.  This now returns a single
        string, which is the expected input format for Gemini.

        Args:
            content (str): Main content for the presentation
            additional_context (dict, optional): Additional context/instructions

        Returns:
            str:  The complete prompt string.
        """
        prompt_parts = [self.prompt_template, content]

        if additional_context:
            prompt_parts.append(json.dumps(additional_context))

        return "\n\n".join(prompt_parts)


    def generate(
        self, content: str, presentation_config: Optional[Dict] = None
    ) -> Dict[str, Union[str, Path]]:
        """
        Generate a reveal.js presentation.

        Args:
            content (str): Content to create presentation from
            presentation_config (dict, optional): Configuration for the presentation

        Returns:
            dict: Contains generated HTML and save path
        """
        try:
            # Create directory for this presentation
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            task_dir = self.base_dir / timestamp
            task_dir.mkdir(parents=True, exist_ok=True)

            # Build and log the prompt
            prompt = self._build_prompt(content, presentation_config)
            logger.info(f"Generating speech in {task_dir}")


            # Get response from Gemini
            start_time = time.time()
            response = self.model.generate_content(prompt, stream=True)  # Use stream=True


            # Collect the response
            output = ""
            for chunk in response:
                try: # Add try-except block to handle potential errors when accessing chunk.text
                    if chunk.text: # Check if chunk.text is not None or empty
                        output += chunk.text
                    else:
                        logger.warning(f"Chunk with no text content encountered. Finish reason: {chunk.finish_reason}") # Log warning if no text
                except ValueError as e: # Catch ValueError if chunk.text access fails
                    logger.error(f"Error accessing chunk.text: {e}. Finish reason: {chunk.finish_reason}")
                logger.debug(f"Processing time: {time.time()-start_time:.2f}s")

            # Validate the output
            if not self._validate_html(output):
                raise ValueError("Generated HTML is not valid reveal.js presentation")

            # Save the presentation
            output_path = task_dir / "presentation.html"
            with open(output_path, "w") as f:
                output = output.replace("```html", "").replace("```", "")
                f.write(output)

            process_html(output_path)

            logger.info(f"Script generated successfully in {task_dir}")

            return {"html": output, "path": output_path}

        except Exception as e:
            logger.error(f"Error generating Script: {e}")
            raise

    def batch_generate(
        self, contents: List[str], configs: Optional[List[Dict]] = None
    ) -> List[Dict[str, Union[str, Path]]]:
        """
        Generate multiple presentations in batch.

        Args:
            contents (list): List of content strings
            configs (list, optional): List of presentation configs

        Returns:
            list: List of generation results
        """
        if configs and len(contents) != len(configs):
            raise ValueError("Number of contents and configs must match")

        results = []
        for i, content in enumerate(contents):
            config = configs[i] if configs else None
            result = self.generate(content, config)
            results.append(result)

        return results


class PresentationGenerator:
    """A class to generate reveal.js presentations using Google's Gemini API."""

    def __init__(self, save_dir: str = "./"):
        """
        Initialize the PresentationGenerator.

        Args:
            save_dir (str): Directory to save generated presentations
        """
        dotenv.load_dotenv()
        
        self.api_key = open("gem.api", "r").read()

        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-2.0-pro-exp-02-05')  # Or an appropriate model
        self.base_dir = Path(save_dir) / "presentations"
        self.base_dir.mkdir(parents=True, exist_ok=True)

        # Load system prompt template
        prompt_path = Path(__file__).parent / "prompt_template.txt"
        with open(prompt_path, "r") as f:
            self.prompt_template = f.read()

    def _validate_html(self, html_content: str) -> bool:
        """
        Validate the generated HTML content.

        Args:
            html_content (str): HTML content to validate

        Returns:
            bool: True if valid, False otherwise
        """
        try:
            soup = BeautifulSoup(html_content, "html.parser")
            # Check for required reveal.js elements
            if not soup.find("div", class_="reveal"):
                return False
            if not soup.find("div", class_="slides"):
                return False
            if not soup.find_all("section"):
                return False
            return True
        except Exception as e:
            logger.error(f"HTML validation error: {e}")
            return False

    def _build_prompt(
        self, content: str, additional_context: Optional[Dict] = None
    ) -> str:
        """
        Build the prompt for the Gemini API.  This now returns a single
        string, which is the expected input format for Gemini.

        Args:
            content (str): Main content for the presentation
            additional_context (dict, optional): Additional context/instructions

        Returns:
            str:  The complete prompt string.
        """
        prompt_parts = [self.prompt_template, content]

        if additional_context:
            prompt_parts.append(json.dumps(additional_context))

        return "\n\n".join(prompt_parts)


    def generate(
        self, content: str, presentation_config: Optional[Dict] = None
    ) -> Dict[str, Union[str, Path]]:
        """
        Generate a reveal.js presentation.

        Args:
            content (str): Content to create presentation from
            presentation_config (dict, optional): Configuration for the presentation

        Returns:
            dict: Contains generated HTML and save path
        """
        try:
            # Create directory for this presentation
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            task_dir = self.base_dir / timestamp
            task_dir.mkdir(parents=True, exist_ok=True)

            # Build and log the prompt
            prompt = self._build_prompt(content, presentation_config)
            logger.info(f"Generating presentation in {task_dir}")


            # Get response from Gemini
            start_time = time.time()
            response = self.model.generate_content(prompt, stream=True)  # Use stream=True


            # Collect the response
            output = ""
            for chunk in response:
                try: # Add try-except block to handle potential errors when accessing chunk.text
                    if chunk.text: # Check if chunk.text is not None or empty
                        output += chunk.text
                    else:
                        logger.warning(f"Chunk with no text content encountered. Finish reason: {chunk.finish_reason}") # Log warning if no text
                except ValueError as e: # Catch ValueError if chunk.text access fails
                    logger.error(f"Error accessing chunk.text: {e}. Finish reason: {chunk.finish_reason}")
                logger.debug(f"Processing time: {time.time()-start_time:.2f}s")

            # Validate the output
            if not self._validate_html(output):
                raise ValueError("Generated HTML is not valid reveal.js presentation")

            # Save the presentation
            output_path = task_dir / "presentation.html"
            with open(output_path, "w") as f:
                output = output.replace("```html", "").replace("```", "")
                f.write(output)

            logger.info(f"Presentation generated successfully in {task_dir}")

            return {"html": output, "path": output_path}

        except Exception as e:
            logger.error(f"Error generating presentation: {e}")
            raise

    def batch_generate(
        self, contents: List[str], configs: Optional[List[Dict]] = None
    ) -> List[Dict[str, Union[str, Path]]]:
        """
        Generate multiple presentations in batch.

        Args:
            contents (list): List of content strings
            configs (list, optional): List of presentation configs

        Returns:
            list: List of generation results
        """
        if configs and len(contents) != len(configs):
            raise ValueError("Number of contents and configs must match")

        results = []
        for i, content in enumerate(contents):
            config = configs[i] if configs else None
            result = self.generate(content, config)
            results.append(result)

        return results


if __name__ == "__main__":
    # Example usage
    # generator = PresentationGenerator()
    script_generator = ScriptGenerator()

    # content = open("scripts/script.txt", "r").read()

    with open("scripts/raw_script.txt", "r") as f:
        raw_content = f.read()

    # result = generator.generate(content)
    # print(f"Presentation generated at: {result['path']}")

    result = script_generator.generate(raw_content)
    print(f"Script Generated at: {result['path']}")