# Startup Information Scraper using Claude Sonnet 4 API
# This script allows users to search for information about startups using the Anthropic Claude Sonnet 4 API.
# It retrieves details such as description, hiring status, and contact information, and formats the output

import os
import json
from anthropic import Anthropic
from dotenv import load_dotenv


class StartupSearcher:
    def __init__(self, api_key=None):
        """
        Initialize the StartupSearcher with Claude API key.

        Args:
            api_key (str): Your Anthropic API key. If None, will look for ANTHROPIC_API_KEY env var.
        """
        load_dotenv()
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError(
                "API key is required. Set ANTHROPIC_API_KEY environment variable or pass api_key parameter."
            )

        self.client = Anthropic(api_key=self.api_key)

    def search_startup_info(self, startup_name):
        """
        Search for startup information using Claude Sonnet 4.

        Args:
            startup_name (str): Name of the startup to search for

        Returns:
            dict: Dictionary containing startup information
        """

        prompt = f"""Please search the web for information about the startup "{startup_name}" and provide:

1. A short paragraph (2-3 sentences) describing what they do
2. Whether they are currently hiring (yes/no/unknown)
3. Contact information (email, website, social media, etc.)

Please format your response as a JSON object with the following structure:
{{
    "startup_name": "{startup_name}",
    "description": "Brief description of what they do",
    "keywords": ["keyword1", "keyword2", ...],
    "hiring_status": "yes/no/unknown",
    "contact_info": {{
        "website": "URL if found",
        "email": "email if found", 
        "linkedin": "LinkedIn URL if found",
        "twitter": "Twitter/X handle if found",
        "other": "Any other contact methods"
    }}
}}

If you cannot find certain information, use "Not found" as the value."""

        try:
            response = self.client.messages.create(
                model="claude-3-7-sonnet-20250219",
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}],
            )

            # Extract the response content
            response_text = response.content[0].text

            # Try to parse JSON from the response
            try:
                # Look for JSON in the response
                start_idx = response_text.find("{")
                end_idx = response_text.rfind("}") + 1

                if start_idx != -1 and end_idx != -1:
                    json_str = response_text[start_idx:end_idx]
                    startup_info = json.loads(json_str)
                else:
                    # If no JSON found, create a structured response
                    startup_info = {
                        "startup_name": startup_name,
                        "description": response_text,
                        "hiring_status": "unknown",
                        "contact_info": {
                            "website": "Not found",
                            "email": "Not found",
                            "linkedin": "Not found",
                            "twitter": "Not found",
                            "other": "Not found",
                        },
                    }

                return startup_info

            except json.JSONDecodeError:
                # If JSON parsing fails, return raw response in structured format
                return {
                    "startup_name": startup_name,
                    "description": response_text,
                    "hiring_status": "unknown",
                    "contact_info": {
                        "website": "Not found",
                        "email": "Not found",
                        "linkedin": "Not found",
                        "twitter": "Not found",
                        "other": "Not found",
                    },
                    "raw_response": response_text,
                }

        except Exception as e:
            return {
                "startup_name": startup_name,
                "error": f"Failed to search for startup: {str(e)}",
                "description": "Error occurred during search",
                "hiring_status": "unknown",
                "contact_info": {
                    "website": "Not found",
                    "email": "Not found",
                    "linkedin": "Not found",
                    "twitter": "Not found",
                    "other": "Not found",
                },
            }

    def print_startup_info(self, startup_info):
        """
        Pretty print the startup information.

        Args:
            startup_info (dict): Startup information dictionary
        """
        print(f"\n{'='*50}")
        print(f"STARTUP: {startup_info['startup_name']}")
        print(f"{'='*50}")

        if "error" in startup_info:
            print(f"❌ Error: {startup_info['error']}")
            return

        print(f"\n📋 DESCRIPTION:")
        print(f"   {startup_info['description']}")

        print(f"\n💼 HIRING STATUS:")
        hiring_emoji = (
            "✅"
            if startup_info["hiring_status"].lower() == "yes"
            else "❌" if startup_info["hiring_status"].lower() == "no" else "❓"
        )
        print(f"   {hiring_emoji} {startup_info['hiring_status'].capitalize()}")

        print(f"\n📞 CONTACT INFORMATION:")
        contact_info = startup_info.get("contact_info", {})

        for key, value in contact_info.items():
            if value and value != "Not found":
                emoji_map = {
                    "website": "🌐",
                    "email": "📧",
                    "linkedin": "💼",
                    "twitter": "🐦",
                    "other": "📱",
                }
                emoji = emoji_map.get(key, "📱")
                print(f"   {emoji} {key.capitalize()}: {value}")


def main():
    """
    Main function to demonstrate usage of the StartupSearcher.
    """
    try:
        # Initialize the searcher
        searcher = StartupSearcher()

        # Get startup name from user
        startup_name = input("Enter the name of the startup to search for: ").strip()

        if not startup_name:
            print("Please enter a valid startup name.")
            return

        print(f"\n🔍 Searching for information about '{startup_name}'...")
        print("This may take a moment...")

        # Search for startup info
        startup_info = searcher.search_startup_info(startup_name)

        # Print the results
        searcher.print_startup_info(startup_info)

        # Optionally save to file
        save_to_file = (
            input("\nWould you like to save this information to a JSON file? (y/n): ")
            .strip()
            .lower()
        )
        if save_to_file == "y":
            filename = f"{startup_name.replace(' ', '_').lower()}_info.json"
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(startup_info, f, indent=2, ensure_ascii=False)
            print(f"✅ Information saved to {filename}")

    except ValueError as e:
        print(f"❌ Configuration Error: {e}")
        print("\nTo use this script, you need to:")
        print("1. Get an API key from https://console.anthropic.com/")
        print(
            "2. Set it as an environment variable: export ANTHROPIC_API_KEY='your-key-here'"
        )
        print(
            "3. Or pass it directly when creating StartupSearcher(api_key='your-key')"
        )

    except Exception as e:
        print(f"❌ Unexpected error: {e}")


if __name__ == "__main__":
    main()
