from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from typing import Dict, Any, Optional, List
import re
import json
from urllib.parse import urljoin, urlparse
import logging
import sys
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        # logging.FileHandler(f'scraper_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger('ComponentScraper')

class ComponentScraper:
    def __init__(self):
        self.base_url = "https://www.saltdesignsystem.com"
        self.playwright = None
        logger.info("Initialized ComponentScraper")
    
    async def __aenter__(self):
        logger.info("Starting Playwright")
        self.playwright = await async_playwright().start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.playwright:
            logger.info("Stopping Playwright")
            await self.playwright.stop()
    
    async def scrape_component(self, url: str) -> Dict[str, Any]:
        """Scrape component information from Salt Design System pages."""
        logger.info(f"Starting to scrape component from URL: {url}")
        
        try:
            async with async_playwright() as p:
                logger.info("Launching browser")
                browser = await p.chromium.launch(headless=False, slow_mo=500)
                page = await browser.new_page()
                
                # Extract component name from URL
                component_name = self._extract_component_name(url)
                logger.info(f"Extracted component name: {component_name}")
                
                # Scrape usage page
                usage_url = self._get_usage_url(url)
                logger.info(f"Scraping usage page: {usage_url}")
                await page.goto(usage_url)
                await page.wait_for_load_state("networkidle")
                usage_content = await page.content()
                usage_soup = BeautifulSoup(usage_content, 'html.parser')
                
                # Scrape examples page
                examples_url = self._get_examples_url(url)
                logger.info(f"Scraping examples page: {examples_url}")
                await page.goto(examples_url)
                await page.wait_for_load_state("networkidle")
                
                # Click all "Show code" buttons
                logger.info("Clicking 'Show code' buttons")
                await self._click_show_code_buttons(page)
                
                examples_content = await page.content()
                examples_soup = BeautifulSoup(examples_content, 'html.parser')
                
                # Extract component information
                logger.info("Extracting component information")
                component_info = {
                    "component_name": component_name,
                    "metadata": {
                        "component_name": component_name,
                        "description": self._extract_description(usage_soup),
                        "props": self._extract_props(usage_soup),
                        "examples": self._extract_examples(examples_soup),
                        "category": self._extract_category(usage_soup),
                        "tags": self._extract_tags(usage_soup),
                        "when_to_use": self._extract_when_to_use(usage_soup),
                        "when_not_to_use": self._extract_when_not_to_use(usage_soup),
                        "import_statement": self._extract_import_statement(usage_soup)
                    },
                    "documentation_url": url
                }
                
                logger.info("Successfully extracted component information")
                await browser.close()
                return component_info
                
        except Exception as e:
            logger.error(f"Error scraping component: {str(e)}", exc_info=True)
            raise
    
    def _extract_component_name(self, url: str) -> str:
        """Extract component name from URL."""
        try:
            path = urlparse(url).path
            parts = path.split('/')
            # The component name is in the 'components' section of the path
            component_index = parts.index('components') + 1
            if component_index < len(parts):
                name = parts[component_index].capitalize()
                logger.debug(f"Extracted component name '{name}' from URL: {url}")
                return name
            logger.warning(f"Could not find component name in URL path: {path}")
            return "Unknown Component"
        except Exception as e:
            logger.error(f"Error extracting component name: {str(e)}")
            return "Unknown Component"
    
    def _get_usage_url(self, url: str) -> str:
        """Get the usage page URL."""
        usage_url = url.replace('/examples', '/usage')
        logger.debug(f"Generated usage URL: {usage_url}")
        return usage_url
    
    def _get_examples_url(self, url: str) -> str:
        """Get the examples page URL."""
        examples_url = url.replace('/usage', '/examples')
        logger.debug(f"Generated examples URL: {examples_url}")
        return examples_url
    
    async def _click_show_code_buttons(self, page) -> None:
        """Click all 'Show code' switches on the page."""
        try:
            # Select all saltSwitch labels
            labels = await page.query_selector_all('label.saltSwitch')

            logger.info(f"Found {len(labels)} switches in total")

            count = 0
            for i, label in enumerate(labels):
                text = await label.query_selector('.saltSwitch-label')
                text_content = await text.text_content() if text else ""

                if "show code" in text_content.lower():
                    logger.debug(f"Clicking 'Show code' switch {i+1}")
                    switch_input = await label.query_selector('input[type="checkbox"]')
                    if switch_input:
                        await switch_input.click()
                        count += 1
                        await page.wait_for_timeout(500)  # wait for code block to appear

            logger.info(f"Clicked {count} 'Show code' switches")
            await page.wait_for_timeout(1000)  # ensure all blocks are rendered

        except Exception as e:
            logger.error(f"Error clicking 'Show code' switches: {e}")

    
    def _extract_description(self, soup: BeautifulSoup) -> str:
        """Extract component description."""
        try:
            # Find the first paragraph after the h1
            h1 = soup.find('h1')
            if h1:
                next_elem = h1.find_next('p')
                if next_elem:
                    description = next_elem.text.strip()
                    logger.debug(f"Extracted description: {description[:100]}...")
                    return description
            logger.warning("No description found")
            return ""
        except Exception as e:
            logger.error(f"Error extracting description: {str(e)}")
            return ""
    
    def _extract_props(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract component props/API documentation."""
        props = []
        try:
            # Find the Props section
            props_section = soup.find(string=re.compile(r'Props', re.IGNORECASE))
            if props_section:
                # Find the table after the Props heading
                table = props_section.find_next('table')
                if table:
                    rows = table.find_all('tr')[1:]  # Skip header row
                    logger.info(f"Found {len(rows)} prop rows")
                    
                    for row in rows:
                        cells = row.find_all(['td', 'th'])
                        if len(cells) >= 3:
                            prop = {
                                'name': cells[0].text.strip(),
                                'type': cells[1].text.strip(),
                                'description': cells[2].text.strip(),
                                'required': 'required' in cells[0].text.lower(),
                                'default': cells[3].text.strip() if len(cells) > 3 else None
                            }
                            props.append(prop)
                            logger.debug(f"Extracted prop: {prop['name']}")
            else:
                logger.warning("No props section found")
        except Exception as e:
            logger.error(f"Error extracting props: {str(e)}")
        return props
    
    def _extract_examples(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Extract component examples and code snippets."""
        examples = []
        try:
            # Find all <pre><code> blocks (after clicking "Show code" switches)
            code_blocks = soup.find_all('pre', class_=re.compile(r'shiki'))

            logger.info(f"Found {len(code_blocks)} code blocks")

            for i, code_block in enumerate(code_blocks):
                # Traverse upward to find the container with heading and optional description
                container = code_block.find_parent()

                # Try to find a heading tag in the parent or grandparent containers
                heading = None
                desc = ""
                for ancestor in code_block.parents:
                    heading = ancestor.find(['h2', 'h3', 'h4'])
                    if heading:
                        desc_elem = heading.find_next_sibling('p')
                        if desc_elem and desc_elem.name == 'p':
                            desc = desc_elem.get_text(strip=True)
                        break

                # Get heading text
                heading_text = heading.get_text(strip=True) if heading else f"Example {i + 1}"

                # Extract the code text from the code block
                code_elem = code_block.find('code')
                jsx = code_elem.get_text(strip=True) if code_elem else code_block.get_text(strip=True)

                examples.append({
                    'title': heading_text,
                    'description': desc,
                    'jsx': jsx
                })
                logger.debug(f"Extracted example: {heading_text[:50]}...")

            logger.info(f"Successfully extracted {len(examples)} examples")
            return examples

        except Exception as e:
            logger.error(f"Error extracting examples: {str(e)}", exc_info=True)
            return []

    
    def _extract_category(self, soup: BeautifulSoup) -> str:
        """Extract component category."""
        try:
            # Look for category in navigation or breadcrumbs
            nav = soup.find('nav')
            if nav:
                category_elem = nav.find('a', class_=re.compile(r'category|type'))
                if category_elem:
                    category = category_elem.text.strip()
                    logger.debug(f"Extracted category: {category}")
                    return category
            logger.warning("No category found, using default")
            return "Components"
        except Exception as e:
            logger.error(f"Error extracting category: {str(e)}")
            return "Components"
    
    def _extract_tags(self, soup: BeautifulSoup) -> List[str]:
        """Extract component tags."""
        tags = set()
        try:
            # Extract tags from various sources
            tag_containers = soup.find_all(['div', 'span'], class_=re.compile(r'tags|keywords'))
            for container in tag_containers:
                tag_elems = container.find_all(['span', 'a'])
                tags.update(tag.text.strip().lower() for tag in tag_elems)
            
            # Add common tags based on component name
            component_name = self._extract_component_name(soup.find('h1').text)
            tags.add(component_name.lower())
            
            logger.info(f"Extracted {len(tags)} tags: {', '.join(sorted(tags))}")
            return sorted(list(tags))
        except Exception as e:
            logger.error(f"Error extracting tags: {str(e)}")
            return []
    
    def _extract_when_to_use(self, soup: BeautifulSoup) -> List[str]:
        """Extract when to use guidelines."""
        guidelines = []
        try:
            # Find the "When to use" section
            when_to_use = soup.find(string=re.compile(r'When to use', re.IGNORECASE))
            if when_to_use:
                # Get all list items after the heading
                items = when_to_use.find_next('ul').find_all('li')
                guidelines = [item.text.strip() for item in items]
                logger.info(f"Extracted {len(guidelines)} 'when to use' guidelines")
            else:
                logger.warning("No 'when to use' section found")
        except Exception as e:
            logger.error(f"Error extracting 'when to use' guidelines: {str(e)}")
        return guidelines
    
    def _extract_when_not_to_use(self, soup: BeautifulSoup) -> List[str]:
        """Extract when not to use guidelines."""
        guidelines = []
        try:
            # Find the "When not to use" section
            when_not_to_use = soup.find(string=re.compile(r'When not to use', re.IGNORECASE))
            if when_not_to_use:
                # Get all list items after the heading
                items = when_not_to_use.find_next('ul').find_all('li')
                guidelines = [item.text.strip() for item in items]
                logger.info(f"Extracted {len(guidelines)} 'when not to use' guidelines")
            else:
                logger.warning("No 'when not to use' section found")
        except Exception as e:
            logger.error(f"Error extracting 'when not to use' guidelines: {str(e)}")
        return guidelines
    
    def _extract_import_statement(self, soup: BeautifulSoup) -> str:
        """Extract import statement from the usage page."""
        try:
            # Find the Import section
            import_section = soup.find(string=re.compile(r'Import', re.IGNORECASE))
            if import_section:
                # Get the code block after the Import heading
                code_block = import_section.find_next('pre') or import_section.find_next('code')
                if code_block:
                    import_statement = code_block.text.strip()
                    logger.debug(f"Extracted import statement: {import_statement}")
                    return import_statement
            logger.warning("No import statement found")
            return ""
        except Exception as e:
            logger.error(f"Error extracting import statement: {str(e)}")
            return "" 