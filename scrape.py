"""
usage:
    python scrape.py <output file path> <data dir path> <page limit> <skip page count>

This program reads a file of GOLD ids downloaded from genomesonline.org (but
maybe no longer available).  If the web page associated with a GOLD id has
been saved as a file then that file is parsed.  If the page has not been saved
then a request is made for the web page, the page is saved as a file, then it
is loaded and parsed.

This script requires BeautifulSoup4.
"""

import collections
import os.path
import sys

import bs4
import requests


def scrape(output_file_path, data_cache_dir_path, limit=0, skip=0):
    with open('gold_bacteria.csv') as gold:
        # first row is a header
        header = gold.readline()
        print('skipping {} lines'.format(skip))
        for skip_line in range(0, skip):
            gold.readline()
        for row_index, line in enumerate(gold.readlines()):
            if row_index > limit > 0:
                break
            row = line.strip().split('\t')
            # strip the quotes
            goldstamp = row[0][1:-1]
            print('{} goldstamp: {}'.format(row_index + skip, goldstamp))

            metadata = get_gold_metadata(goldstamp, data_cache_dir_path)
            print(metadata)

            output_file_exists = os.path.isfile(output_file_path)
            with open(output_file_path, 'a') as output_file:
                if not output_file_exists:
                    # write a header
                    output_file.write('\t'.join(metadata.keys()))
                    output_file.write('\n')
                output_file.write('\t'.join(metadata.values()))
                output_file.write('\n')


def get_gold_metadata(goldstamp, data_cache_dir_path):
    gold_html_file_path = '{}/{}.html'.format(data_cache_dir_path, goldstamp)
    if os.path.isfile(gold_html_file_path):
        print('already have {}'.format(goldstamp))
        with open(gold_html_file_path) as html_file:
            soup = bs4.BeautifulSoup(html_file.read())
            metadata = parse_soup_to_metadata(soup)
    else:
        metadata = read_metadata_for_goldstamp(goldstamp, gold_html_file_path)
    return metadata


def read_metadata_for_goldstamp(goldstamp, html_file_path):
    # a goldstamp looks like Gi0046999
    response = requests.get('http://genomesonline.org/cgi-bin/GOLD/GOLDCards.cgi?goldstamp={}'.format(goldstamp))
    soup = bs4.BeautifulSoup(response.text)
    with open(html_file_path, 'w') as html:
        try:
            html.write(soup.prettify(formatter='html'))
        except:
            print('failed to write {}'.format(html_file_path))
    metadata = parse_soup_to_metadata(soup)
    return metadata


def parse_soup_to_metadata(soup):
    # read HTML table header tags to get keys
    # read HTML table data tags to get data
    # record all the data on this page in the metadata dictionary
    metadata = collections.OrderedDict()
    all_th_tags = soup.find_all('th')
    for th_tag in all_th_tags:
        for b in th_tag.find_all('b'):
            key = b.text.strip()
            td_tag = th_tag.parent.find('td')
            if td_tag is None:
                value = 'None'
            else:
                td_child = td_tag.find()
                if td_child is None:
                    if td_tag.string is None:
                        value = 'None'
                    else:
                        value = td_tag.string
                elif td_child.string is None:
                    value = 'None'
                else:
                    value = td_child.string
            value = value.strip()
            if len(value) == 0:
                value = 'None'
            metadata[key] = value.encode('ascii', 'backslashreplace')
    return metadata


if __name__ == '__main__':
    scrape(sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]))