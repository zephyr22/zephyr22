import os
import sys
import datetime
import numpy as np
import pickle
import pandas as pd
import time
import logging
import datetime
import PIR_URLParser


def main(start_url=r"https://tpirepguide.com/?p=18052", start_id='9782K'):
    data_basics = []
    data_showcase = []
    showcase_missing = []
    set_up_folders()
    today_date = datetime.datetime.now().date()
    logger = set_up_logging(today_date)
    next_url = None
    try:
        keep_going = True
        while keep_going:
            pir_base = PIR_URLParser.PriceIsRightBasics(start_url, start_id)
            pir_base.get_page_content()
            time.sleep(2)
            logger.info("Parsing {0}: {1}".format(start_url, start_id))
            cnt = 0
            while pir_base.soup is None and cnt < 3:
                pir_base.get_page_content()
                cnt += 1
                time.sleep(2)
                logger.info(r"Failed to get soup: {0}".format(cnt))
            if pir_base.soup is None:
                return
            pir_base.get_next_url()
            pir_base.get_date()
            time.sleep(1)
            data_basics.append([pir_base.current_url, pir_base.current_id, pir_base.error_code,
                                pir_base.footer_data])
            # Main Content Retrieval
            pir_parsing = PIR_URLParser.ParsePIRContent(pir_base.soup, start_id)
            pir_parsing.get_showcase_information()
            if len(pir_parsing.dfs) > 0:
                data_showcase += pir_parsing.dfs
            else:
                # Note failed to get showcase info
                showcase_missing.append([start_url, pir_parsing.stop_reason])
                logger.info("Showcase Missing: {0}".format(pir_parsing.stop_reason))
            if pir_parsing.error_code is not None:
                showcase_missing.append([start_url, pir_parsing.error_code])
                logger.info("Showcase Missing: {0}".format(pir_parsing.error_code))
            time.sleep(1)
            with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), r"pir_pickle.pkl"), 'wb') as my_file:
                pickle.dump([data_basics, data_showcase, showcase_missing], my_file)
            if pir_base.next_url is None or pir_base.next_url == pir_base.current_url:
                return
            start_url = pir_base.next_url
            start_id = pir_base.next_label
    except:
        print("Exception: ", start_url, start_id)
        save_progress(data_basics, data_showcase, showcase_missing)
        print(next_url)
    finally:
        # Save Progess
        save_progress(data_basics, data_showcase, showcase_missing)
        print(next_url)


def save_progress(data_basics, data_showcase, showcase_missing):
    df = pd.DataFrame(data_basics, columns=['url', 'episodeID', 'errorCode', 'footer'])
    # Additional Column
    df['urlParam'] = df.url.apply(lambda x: x.split("=")[1])
    df['EpsCategory'] = df.footer.apply(lambda x: x.split(":")[1].strip())
    df['airDate'] = df.footer.apply(lambda x: x.split("|")[0].strip())
    check_for_file_and_save(r"Data\pir_Check.csv", df)
    # save content data
    if len(data_showcase) > 0:
        error_dfs = []
        for i in range(0, len(data_showcase)):
            show_seg = data_showcase[i]
            tot = sum([1 if x in show_seg.columns[j + 1:] else 0 for j, x in enumerate(show_seg.columns)])
            if tot > 0:
                error_dfs.append(i)
        data_showcase = [x for i, x in enumerate(data_showcase) if i not in error_dfs]
        data_showcase = pd.concat(data_showcase, ignore_index=True)
        check_for_file_and_save(r"Data\pir_Content.csv", data_showcase)
    # save error reasons
    df = pd.DataFrame(showcase_missing, columns=['url', 'reason'])
    check_for_file_and_save(r"Data\pir_ErrorContent.csv", df)


def check_for_file_and_save(file_name, df):
    directory = os.path.dirname(os.path.abspath(__file__))
    full_path = os.path.join(directory, file_name)
    if os.path.exists(full_path) and os.path.isfile(full_path):
        old_df = pd.read_csv(full_path)
        if len(old_df) > 0:
            df = pd.concat([old_df, df], ignore_index=True)
    df.to_csv(full_path, index=False, header=True)


def set_up_logging(today_date):
    """Create the logger for logging"""
    directory = os.path.dirname(os.path.abspath(__file__))
    # Create Logger
    logger = logging.getLogger('PriceIsRight')
    logger.setLevel(logging.INFO)
    # Create Handlers
    log_file = os.path.join(directory, r'Logs\PriceIsright_{}.log'.format(today_date))
    f_handler = logging.FileHandler(log_file)
    f_handler.setLevel(logging.INFO)
    # Add Formatting and add to handler
    f_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    f_handler.setFormatter(f_format)
    # Add handler to Logger
    logger.addHandler(f_handler)
    return logger


def set_up_folders():
    directory = os.path.dirname(os.path.abspath(__file__))
    for dir_name in ['Logs', 'Data']:
        dir_path = os.path.join(directory, dir_name)
        if os.path.exists(dir_path) and os.path.isdir(dir_path):
            pass
        else:
            os.makedirs(dir_path)
            print('Created Directory: {}'.format(dir_path))
    return directory


if __name__ == "__main__":
    num_params = len(sys.argv)
    if num_params < 2:
        print("No Parameters Supplied, using defaults.")
        main()
    elif num_params == 3:
        url = str(sys.argv[1])
        url_id = str(sys.argv[2])
        print("Starting with: ", url, " ", url_id)
        main(url, url_id)
    else:
        print("Incorrect Number of Parameters Supplied, P1: URL to start with, P2: ID from URL page")
