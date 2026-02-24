import os
import json
from datetime import datetime
from fpdf import FPDF
from collections import Counter

class ReportGenerator:
    def __init__(self, db):
        self.db = db

    def generate_all(self, run_results):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        run_id = run_results['run_id']
        
        md_path = self.generate_markdown(run_results, timestamp)
        pdf_path = self.generate_pdf(run_results, timestamp)
        stats_path = self.generate_stats()
        
        return md_path, pdf_path, stats_path

    def generate_markdown(self, results, timestamp):
        os.makedirs("reports", exist_ok=True)
        filename = f"reports/run_{timestamp}.md"
        
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"# QuotePulse Run Report\n\n")
            f.write(f"- **Run ID:** {results['run_id']}\n")
            f.write(f"- **Timestamp:** {datetime.now().isoformat()}\n")
            f.write(f"- **Pages Scraped:** {results['pages_scraped']}\n")
            f.write(f"- **Total Quotes Seen:** {results['total_seen']}\n\n")
            
            f.write(f"## Summary\n")
            f.write(f"- **New Quotes:** {len(results['new_quotes'])}\n")
            f.write(f"- **Changed Quotes (Tags):** {len(results['changed_quotes'])}\n")
            f.write(f"- **Disappeared Quotes:** {len(results['disappeared_quotes'])}\n\n")
            
            if results['new_quotes']:
                f.write(f"## New Quotes (Sample 10)\n")
                for q in results['new_quotes'][:10]:
                    f.write(f"- \"{q['quote_text']}\" — **{q['author_name']}**\n")
            
            if results['changed_quotes']:
                f.write(f"## Changed Quotes\n")
                for q in results['changed_quotes']:
                    f.write(f"- \"{q['quote_text']}\" — **{q['author_name']}** (Tags updated)\n")

        return filename

    def generate_pdf(self, results, timestamp):
        os.makedirs("reports", exist_ok=True)
        filename = f"reports/run_{timestamp}.pdf"
        
        class StyledPDF(FPDF):
            def header(self):
                self.set_fill_color(52, 73, 94) # Dark blue/gray
                self.rect(0, 0, 210, 40, 'F')
                self.set_text_color(255, 255, 255)
                self.set_font("Helvetica", "B", 24)
                self.cell(0, 30, "QuotePulse Report", align='C', ln=True)
                self.ln(10)

            def footer(self):
                self.set_y(-15)
                self.set_font("Helvetica", "I", 8)
                self.set_text_color(128, 128, 128)
                self.cell(0, 10, f"Page {self.page_no()} | Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}", align='C')

        pdf = StyledPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        
        # Metadata Section
        pdf.set_y(50)
        pdf.set_text_color(44, 62, 80)
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(40, 10, "Run ID:", ln=0)
        pdf.set_font("Helvetica", "", 12)
        pdf.cell(0, 10, f"{results['run_id']}", ln=1)
        
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(40, 10, "Pages Scraped:", ln=0)
        pdf.set_font("Helvetica", "", 12)
        pdf.cell(0, 10, f"{results['pages_scraped']}", ln=1)
        
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(40, 10, "Total Quotes Seen:", ln=0)
        pdf.set_font("Helvetica", "", 12)
        pdf.cell(0, 10, f"{results['total_seen']}", ln=1)
        
        pdf.ln(10)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(10)

        # Summary Table-like structure
        pdf.set_font("Helvetica", "B", 16)
        pdf.set_fill_color(236, 240, 241)
        pdf.cell(0, 12, " Scraping Summary", ln=True, fill=True)
        pdf.ln(5)
        
        pdf.set_font("Helvetica", "", 12)
        
        def add_summary_line(label, value, color=(0,0,0)):
            pdf.set_text_color(*color)
            pdf.set_font("Helvetica", "B", 12)
            pdf.cell(60, 10, f"  {label}:", ln=0)
            pdf.set_font("Helvetica", "", 12)
            pdf.cell(0, 10, str(value), ln=1)
            pdf.set_text_color(44, 62, 80)

        add_summary_line("New Quotes", len(results['new_quotes']), (39, 174, 96)) # Green
        add_summary_line("Changed Quotes", len(results['changed_quotes']), (243, 156, 18)) # Orange
        add_summary_line("Disappeared Quotes", len(results['disappeared_quotes']), (192, 57, 43)) # Red
        
        pdf.ln(10)

        # New Quotes Section
        if results['new_quotes']:
            pdf.set_font("Helvetica", "B", 16)
            pdf.set_fill_color(236, 240, 241)
            pdf.cell(0, 12, " New Quotes Sample", ln=True, fill=True)
            pdf.ln(5)
            
            for q in results['new_quotes'][:10]:
                pdf.set_font("Helvetica", "I", 11)
                text = f"\"{q['quote_text']}\""
                text = text.encode('latin-1', 'replace').decode('latin-1')
                pdf.multi_cell(0, 7, text)
                
                pdf.set_font("Helvetica", "B", 10)
                pdf.set_text_color(127, 140, 141)
                author = f"-- {q['author_name']}"
                author = author.encode('latin-1', 'replace').decode('latin-1')
                pdf.cell(0, 6, author, ln=True, align='R')
                pdf.ln(4)
                pdf.set_text_color(44, 62, 80)

        pdf.output(filename)
        return filename

    def generate_stats(self):
        os.makedirs("exports", exist_ok=True)
        quotes = self.db.get_all_quotes()
        
        authors = [q['author_name'] for q in quotes]
        tags = []
        for q in quotes:
            tags.extend(json.loads(q['tags_json']))
            
        author_counts = Counter(authors)
        tag_counts = Counter(tags)
        
        stats = {
            "total_quotes": len(quotes),
            "top_authors": dict(author_counts.most_common(100)),
            "top_tags": dict(tag_counts.most_common(100)),
            "quotes_per_author_distribution": dict(author_counts)
        }
        
        filename = "exports/stats.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(stats, f, indent=4)
            
        # Also update summary.md as requested
        self.generate_summary_md(stats)
        
        return filename

    def generate_summary_md(self, stats):
        os.makedirs("reports", exist_ok=True)
        with open("reports/summary.md", "w", encoding="utf-8") as f:
            f.write("# QuotePulse Global Summary\n\n")
            f.write(f"- **Total Unique Quotes:** {stats['total_quotes']}\n\n")
            
            f.write("## Top 10 Authors\n")
            top_authors = sorted(stats['top_authors'].items(), key=lambda x: x[1], reverse=True)[:10]
            for author, count in top_authors:
                f.write(f"- {author}: {count} quotes\n")
            
            f.write("\n## Top 10 Tags\n")
            top_tags = sorted(stats['top_tags'].items(), key=lambda x: x[1], reverse=True)[:10]
            for tag, count in top_tags:
                f.write(f"- {tag}: {count} occurrences\n")
                
        return "reports/summary.md"
