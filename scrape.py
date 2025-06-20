import os
import json
import time
from datetime import datetime
from startup_searcher import StartupSearcher


class BatchStartupScraper:
    def __init__(self, api_key=None, delay_between_requests=2):
        """
        Initialize the batch scraper.

        Args:
            api_key (str): Anthropic API key
            delay_between_requests (int): Seconds to wait between API calls to avoid rate limits
        """
        self.searcher = StartupSearcher(api_key)
        self.delay = delay_between_requests
        self.results = []

    def read_startup_list(self, filename="list.txt"):
        """
        Read startup names from a text file.

        Args:
            filename (str): Path to the file containing startup names

        Returns:
            list: List of startup names
        """
        try:
            with open(filename, "r", encoding="utf-8") as f:
                startups = [line.strip() for line in f.readlines() if line.strip()]

            print(f"✅ Successfully loaded {len(startups)} startups from {filename}")
            return startups

        except FileNotFoundError:
            print(f"❌ Error: {filename} not found!")
            print(f"Please create a {filename} file with one startup name per line.")
            return []
        except Exception as e:
            print(f"❌ Error reading {filename}: {e}")
            return []

    def scrape_startups(self, startup_list, output_file=None):
        """
        Scrape information for a list of startups.

        Args:
            startup_list (list): List of startup names
            output_file (str): Optional output file to save results

        Returns:
            list: List of startup information dictionaries
        """
        if not startup_list:
            print("No startups to process.")
            return []

        print(f"\n🚀 Starting batch scrape of {len(startup_list)} startups...")
        print(f"⏱️  Estimated time: ~{len(startup_list) * (self.delay + 5)} seconds")
        print("=" * 60)

        results = []

        for i, startup_name in enumerate(startup_list, 1):
            print(f"\n[{i}/{len(startup_list)}] Processing: {startup_name}")

            try:
                # Get startup information
                startup_info = self.searcher.search_startup_info(startup_name)
                results.append(startup_info)

                # Show brief result
                if "error" not in startup_info:
                    status = startup_info.get("hiring_status", "unknown")
                    status_emoji = (
                        "✅"
                        if status.lower() == "yes"
                        else "❌" if status.lower() == "no" else "❓"
                    )
                    print(f"   {status_emoji} Hiring: {status}")

                    website = startup_info.get("contact_info", {}).get(
                        "website", "Not found"
                    )
                    if website != "Not found":
                        print(f"   🌐 Website: {website}")
                else:
                    print(f"   ❌ Error: {startup_info.get('error', 'Unknown error')}")

                # Save progress after each startup (in case of interruption)
                if output_file:
                    self._save_progress(results, output_file)

            except Exception as e:
                error_info = {
                    "startup_name": startup_name,
                    "error": f"Unexpected error: {str(e)}",
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
                results.append(error_info)
                print(f"   ❌ Unexpected error: {e}")

            # Rate limiting delay
            if i < len(startup_list):  # Don't delay after the last request
                print(f"   ⏳ Waiting {self.delay} seconds...")
                time.sleep(self.delay)

        self.results = results
        print(f"\n✅ Batch scrape completed! Processed {len(results)} startups.")
        return results

    def _save_progress(self, results, filename):
        """Save current progress to avoid losing data."""
        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"   ⚠️  Warning: Could not save progress: {e}")

    def save_results(self, results=None, filename=None):
        """
        Save results to JSON file.

        Args:
            results (list): Results to save (uses self.results if None)
            filename (str): Output filename (auto-generated if None)
        """
        if results is None:
            results = self.results

        if not results:
            print("No results to save.")
            return

        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"startup_results_{timestamp}.json"

        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2, ensure_ascii=False)

            print(f"💾 Results saved to: {filename}")
            return filename

        except Exception as e:
            print(f"❌ Error saving results: {e}")
            return None

    def generate_summary_report(self, results=None):
        """
        Generate a summary report of the scraping results.

        Args:
            results (list): Results to analyze (uses self.results if None)
        """
        if results is None:
            results = self.results

        if not results:
            print("No results to analyze.")
            return

        print(f"\n📊 SUMMARY REPORT")
        print("=" * 50)

        total = len(results)
        errors = len([r for r in results if "error" in r])
        successful = total - errors

        # Hiring status analysis
        hiring_yes = len(
            [r for r in results if r.get("hiring_status", "").lower() == "yes"]
        )
        hiring_no = len(
            [r for r in results if r.get("hiring_status", "").lower() == "no"]
        )
        hiring_unknown = total - hiring_yes - hiring_no

        # Contact info analysis
        has_website = len(
            [
                r
                for r in results
                if r.get("contact_info", {}).get("website", "Not found") != "Not found"
            ]
        )
        has_email = len(
            [
                r
                for r in results
                if r.get("contact_info", {}).get("email", "Not found") != "Not found"
            ]
        )

        print(f"📈 Processing Stats:")
        print(f"   Total startups: {total}")
        print(f"   Successful: {successful} ({successful/total*100:.1f}%)")
        print(f"   Errors: {errors} ({errors/total*100:.1f}%)")

        print(f"\n💼 Hiring Status:")
        print(f"   Currently hiring: {hiring_yes} ({hiring_yes/total*100:.1f}%)")
        print(f"   Not hiring: {hiring_no} ({hiring_no/total*100:.1f}%)")
        print(f"   Unknown: {hiring_unknown} ({hiring_unknown/total*100:.1f}%)")

        print(f"\n📞 Contact Info Found:")
        print(f"   Websites: {has_website} ({has_website/total*100:.1f}%)")
        print(f"   Email addresses: {has_email} ({has_email/total*100:.1f}%)")

        # Show companies that are hiring
        hiring_companies = [
            r for r in results if r.get("hiring_status", "").lower() == "yes"
        ]
        if hiring_companies:
            print(f"\n✅ Companies Currently Hiring:")
            for company in hiring_companies[:10]:  # Show up to 10
                name = company.get("startup_name", "Unknown")
                website = company.get("contact_info", {}).get("website", "No website")
                print(f"   • {name} - {website}")

            if len(hiring_companies) > 10:
                print(f"   ... and {len(hiring_companies) - 10} more")


def main():
    """Main function to run the batch scraper."""
    try:
        print("🔍 Batch Startup Information Scraper")
        print("=" * 40)

        # Initialize the scraper
        scraper = BatchStartupScraper(delay_between_requests=2)

        # Read startup list
        startups = scraper.read_startup_list("list.txt")

        if not startups:
            print("\n💡 Create a 'list.txt' file with startup names like this:")
            print("   OpenAI")
            print("   Anthropic")
            print("   Scale AI")
            print("   Replicate")
            return

        # Confirm before starting
        print(f"\nFound {len(startups)} startups to process:")
        for i, startup in enumerate(startups[:5], 1):
            print(f"   {i}. {startup}")
        if len(startups) > 5:
            print(f"   ... and {len(startups) - 5} more")

        proceed = input(f"\nProceed with scraping? (y/n): ").strip().lower()
        if proceed != "y":
            print("Cancelled.")
            return

        # Run the scraper
        results = scraper.scrape_startups(startups)

        # Save results
        output_file = scraper.save_results(results)

        # Generate summary
        scraper.generate_summary_report(results)

        print(f"\n🎉 All done! Check {output_file} for detailed results.")

    except KeyboardInterrupt:
        print("\n\n⏹️  Scraping interrupted by user.")
        if "scraper" in locals() and scraper.results:
            print("Saving partial results...")
            scraper.save_results(scraper.results, "partial_results.json")
            scraper.generate_summary_report(scraper.results)

    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")


if __name__ == "__main__":
    main()
