import html as html_lib
import os
import re
from datetime import datetime

import yaml

BIB_PATH = './data/research/citations.bib'
PROJECTS_PATH = './data/research/projects.yaml'
AUTHORS_PATH = './data/research/author_websites.yaml'
VENUES_PATH = './data/research/venues.yaml'


def read_yaml(file_path):
    """Read YAML file and return its contents."""
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)


def parse_bibfile(file_path):
    """Parse publications.bib into {key: {'raw': verbatim entry, 'fields': {...}}}.

    Assumes the controlled format used in that file: each entry closes with a
    '}' at the start of a line, and field values nest braces at most one level.
    """
    with open(file_path, 'r') as file:
        text = file.read()

    entries = {}
    for match in re.finditer(r'@\w+\s*\{\s*([^,\s]+)\s*,.*?\n\}', text, re.S):
        key = match.group(1)
        fields = {}
        for field in re.finditer(r'(\w+)\s*=\s*\{((?:[^{}]|\{[^{}]*\})*)\}', match.group(0)):
            fields[field.group(1).lower()] = re.sub(r'\s+', ' ', field.group(2)).strip()
        entries[key] = {'raw': match.group(0).strip(), 'fields': fields}
    return entries


def delatex(s):
    """Convert the LaTeX constructs that appear in our bib entries to plain text."""
    for old, new in [(r'$\Omega$', 'Ω'), (r'\Omega', 'Ω'), (r'\&', '&'),
                     ('$', ''), ('{', ''), ('}', '')]:
        s = s.replace(old, new)
    return s


def display_name(bib_author):
    """'Last, First' -> 'First Last'; pass through anything else."""
    parts = [p.strip() for p in bib_author.split(',')]
    if len(parts) == 2:
        return f'{parts[1]} {parts[0]}'
    return bib_author.strip()


def venue_html(venue, year, venue_rules):
    if not venue and not year:
        return ''
    for rule in venue_rules:
        if venue and rule['match'].lower() in venue.lower():
            # Drop a trailing "(ABBR)" from the venue when it repeats the alias
            trailing = re.search(r'\s*\(([^()]*)\)\s*$', venue)
            shown_venue = venue
            if trailing and rule['alias'].replace(' ', '').lower() in trailing.group(1).replace(' ', '').lower():
                shown_venue = venue[:trailing.start()]
            alias = rule['alias'] + (f"'{str(year)[-2:]}" if year else '')
            if rule.get('notable'):
                alias = f'<b>{alias}</b>'
            return f'<em>{shown_venue}</em> ({alias})'
    joiner = ', ' if venue and year else ''
    return f'<em>{venue}</em>{joiner}{year}'


def generate_html(projects, bib_entries, author_websites, author_aliases, venue_rules):
    """Generate the publications HTML from YAML project stubs + bib metadata."""
    html = ""

    for project_key, project in projects.items():
        print(f"Processing project: {project_key}")
        bibkey = project.get('bib')
        entry = bib_entries.get(bibkey)
        if not entry:
            print(f"WARNING: Project '{project_key}' has no bib entry '{bibkey}' in {BIB_PATH}. Skipping.")
            continue

        fields = entry['fields']
        # projects.yaml title/venue/year act as display-only overrides for when the
        # Google Scholar export is wrong or stale; the copied bibtex stays verbatim.
        title = project.get('title') or delatex(fields.get('title', ''))
        authors = [display_name(a) for a in fields.get('author', '').split(' and ') if a.strip()]
        venue = project.get('venue') or delatex(fields.get('booktitle') or fields.get('journal', ''))
        year = project.get('year') or fields.get('year', '')
        thumbnail = project.get('thumbnail', '')
        description = project.get('description', '')
        links = project.get('links', {}) or {}
        paper_link = links.get('paper', '')

        html += f'''
    <tr>
      <td style="padding:20px;width:25%;vertical-align:middle">'''
        if thumbnail:
            html += f'''
        <img src="{thumbnail}" alt="{project_key}_png" style="border-style: none">'''
        html += '''
      </td>
      <td width="75%" valign="middle">'''

        if paper_link:
            html += f'''
        <a href="{paper_link}">
          <span class="papertitle">{title}</span>
        </a>'''
        else:
            html += f'''
        <span class="papertitle">{title}</span>'''

        html += '<br>'

        # Add authors with links: resolve name variants to canonical identities,
        # then link. A missing entry (vs an explicit null) means the site is not
        # findable and gets flagged at compile time.
        authors_html = []
        for author in authors:
            canonical = author_aliases.get(author, author)
            if canonical == "Eric Xing":
                authors_html.append(f'<strong>{canonical}</strong>')
            elif canonical not in author_websites:
                print(f"WARNING: website not findable for author '{author}'"
                      + (f" (canonical: '{canonical}')" if canonical != author else '')
                      + f" — add them to {AUTHORS_PATH}")
                authors_html.append(canonical)
            elif author_websites[canonical]:
                authors_html.append(f'<a href="{author_websites[canonical]}">{canonical}</a>')
            else:
                authors_html.append(canonical)

        html += ',\n        '.join(authors_html)

        if venue or year:
            html += f'<br>\n        {venue_html(venue, year, venue_rules)}'

        # Add links; the bibtex control copies the entry to the clipboard (see index_foot.html)
        links_html = []
        for link_type, link_url in links.items():
            if link_url:
                label = 'arXiv' if link_type.lower() == 'arxiv' else link_type
                links_html.append(f'<a href="{link_url}">{label}</a>')
        links_html.append(f'<a href="#" class="bibtex-copy" data-key="{bibkey}">bibtex</a>')
        html += '<br>\n        ' + ' /\n        '.join(links_html)

        if description:
            html += f'''
        <p>{description}</p>'''

        html += f'''
        <pre class="bibtex-src" id="bib-{bibkey}" hidden>{html_lib.escape(entry['raw'])}</pre>
      </td>
    </tr>
'''
    return html


def main():
    try:
        projects = read_yaml(PROJECTS_PATH)
        bib_entries = parse_bibfile(BIB_PATH)
        author_data = read_yaml(AUTHORS_PATH)
        author_websites = author_data.get('author_websites', {}) or {}
        author_aliases = author_data.get('author_aliases', {}) or {}
        venue_rules = read_yaml(VENUES_PATH).get('venues', [])

        body_html = generate_html(projects, bib_entries, author_websites, author_aliases, venue_rules)

        with open('./index_head.html', 'r') as file:
            head_html = file.read()
        with open('./index_foot.html', 'r') as file:
            foot_html = file.read()

        html = head_html + body_html + foot_html

        backup_dir = './legacy'
        os.makedirs(backup_dir, exist_ok=True)
        backup_file = os.path.join(backup_dir, f'index_{datetime.now().strftime("%Y%m%d_%H%M%S")}.html')

        if os.path.exists('./index.html'):
            os.rename('./index.html', backup_file)

            legacy_files = sorted(os.listdir(backup_dir), key=lambda x: os.path.getmtime(os.path.join(backup_dir, x)))
            if len(legacy_files) > 10:
                for file in legacy_files[:-5]:
                    os.remove(os.path.join(backup_dir, file))
                    print(f"Removed old backup file: {file}")

        with open('./index.html', 'w') as file:
            file.write(html)

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
