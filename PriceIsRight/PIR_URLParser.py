import numpy as np
import pandas as pd
import requests
import re
import time
from bs4 import BeautifulSoup
from requests import ReadTimeout, ConnectTimeout, HTTPError, Timeout, ConnectionError


class PriceIsRightBasics:
    def __init__(self, current_url="https://tpirepguide.com/?p=18052", current_id='9782K'):
        self.current_url = current_url
        self.current_id = current_id
        # For Later Use
        self.soup = None
        self.next_url = None
        self.next_label = None
        self.footer_data = None
        self.error_code = 0
        self.footer_data = None
        self.processed_data = []
            
    def get_page_content(self):
        try:
            page = requests.get(self.current_url)
            self.soup = BeautifulSoup(page.content, "html.parser")
        except (ConnectTimeout, HTTPError, ReadTimeout, Timeout, ConnectionError):
            return

    def get_next_url(self):
        if self.soup is None:
            return
        next_url_html = self.soup.find_all("div", class_="newer")
        next_url_html_len = len(next_url_html)
        if next_url_html_len < 1:
            self.error_code = 1
            return
        next_urls = next_url_html[0].find_all("a", href=True)
        if len(next_urls) < 1:
            self.error_code = 2
            return
        self.next_url = next_urls[0]['href']
        self.next_label = next_urls[0].text
            
    def get_date(self):
        if self.soup is None:
            return
        footer_html = self.soup.find_all("div", class_="post-footer")
        if len(footer_html) < 1:
            return
        self.footer_data = footer_html[0].text


class ParsePIRContent:
    def __init__(self, soup, current_id):
        self.main_content = None
        self.current_id = current_id
        main_content = soup.find_all("div", class_="post-bodycopy clearfix")
        if len(main_content) > 0:
            self.main_content = main_content[0]
        # Later Use
        self.dfs = []
        self.stop_reason = None
        self.error_code = None
                
    def get_showcase_information(self):
        segments = str(self.main_content).split("<hr/>")
        if len(segments) < 6:
            self.stop_reason = "Only {0} hr Segments".format(len(segments))
            return
        for i, seg in enumerate(segments):
            if 'showcase showdown' in seg.lower():
                showcase_seg = BeautifulSoup(seg, "html.parser").text.split("\n")
                showcase_seg = [x for x in showcase_seg if len(x.replace("\t", "")) > 1]
                # Need at least 3 rows, one for each contestant
                if len(showcase_seg) < 3:
                    self.stop_reason = "Not enough showdown rows"
                    return
                else:
                    df = self.process_showcase_segment(showcase_seg)
                    if len(df) > 0:
                        self.dfs.append(df)

    def process_showcase_segment(self, showcase_segment):
        # Showcase segment is a list of lines about the showcase
        showdown = 'SS0'
        segment_lines = []
        data_header = []
        for ind, sc_line in enumerate(showcase_segment):
            sc_line = sc_line.replace('$', "")
            # Split into word segments
            breakdown = sc_line.split()
            breakdown = [x for x in breakdown if len(x) > 0]
            possible_contestant = self.check_if_contestant_line(breakdown)
            if 'showcase showdown' in sc_line.lower():
                showdown = 'SS' + breakdown[-1].replace("#", "")
            elif possible_contestant:
                data_header, c_values = self.process_contestant_line(sc_line)
                data_header = ['SC_ind'] + data_header
                segment_lines.append([ind] + c_values)
        if len(segment_lines) < 1:
            self.stop_reason = "No Contestant lines found"
            return pd.DataFrame()
        # Check have enough headers
        headers_needed = max([len(x) for x in segment_lines])
        diff = headers_needed - len(data_header)
        if diff > 0:
            extra_headers = ['ev' + str(x) for x in range(1, diff + 1, 1)]
            data_header = data_header[:-1] + extra_headers + data_header[-1:]
        segment_lines = self.make_consistent_length(segment_lines, headers_needed)
        df = pd.DataFrame(segment_lines, columns=data_header)
        df['Showcase'] = showdown
        df['urlParam'] = self.current_id
        return df

    @staticmethod
    def check_if_contestant_line(sc_line_breakdown):
        # Check enough segments
        if len(sc_line_breakdown) < 3:
            return False
        # check if first and third segments are numeric,if so keep
        first_seg = re.sub(r"[\.,$\s+]", '', sc_line_breakdown[0])
        third_seg = re.sub(r'[\.,$\s+]', '', sc_line_breakdown[2])
        if first_seg.isnumeric() and third_seg.isnumeric():
            return True
        return False

    @staticmethod
    def check_line_values(line_breakdown):
        # confirm numeric and group comments
        comments = ["C:"]
        line_values = []
        for i, line_seg in enumerate(line_breakdown):
            if line_seg.isnumeric():
                line_values.append(line_seg)
            else:
                comments.append(line_seg)
        comments = (" ").join(comments)
        return line_values + [comments]

    @staticmethod
    def make_consistent_length(contestant_values, max_len):
        contestant_lines = []
        for contestant_line in contestant_values:
            diff = max_len - len(contestant_line)
            if diff > 0:
                # Any comments still last
                contestant_line = contestant_line[:-1] + [None] * diff + contestant_line[-1:]
            contestant_lines.append(contestant_line)
        return contestant_lines

    def process_contestant_line(self, contest_line):
        # Money Won, Name, Spins, if plus sign then 2nd spin value and total before any extra spins
        breakdown = contest_line.split()
        headers = ['PrizeValue', "Contestant", 'Spin1', 'Spin2', 'Total', 'Comments']
        contest_values = breakdown[:3]
        ind = 3
        if len(breakdown) > 3 and breakdown[3] == '+':
            contest_values = contest_values + breakdown[4:6]
            ind = 6
            if len(contest_values) < 5:
                # No total given
                if len(contest_values) > 3:
                    contest_values.append(float(contest_values[2]) + float(contest_values[3]))
                else:
                    contest_values = contest_values + [0, contest_values[2]]
        else:
            contest_values = contest_values + [0, contest_values[2]]
        contest_values = contest_values + self.check_line_values(breakdown[ind:])
        diff = len(headers) - len(contest_values)
        if diff > 0:
            extra_vals = [None] * diff
            contest_values = contest_values + extra_vals
        return headers, contest_values
