import pandas as pd
import os

# define where to save CSV files
BASE_PATH = os.path.join(os.path.dirname(__file__), "exchange_data")
os.makedirs(BASE_PATH, exist_ok=True)

# get directory of THIS file
CURRENT_DIR = os.path.dirname(__file__)

# path to subfolder
DATA_PATH = os.path.join(CURRENT_DIR, "exchange_data")

# URLs for official stock listings
NASDAQ_URL = "ftp://ftp.nasdaqtrader.com/SymbolDirectory/nasdaqlisted.txt"
OTHER_URL = "ftp://ftp.nasdaqtrader.com/SymbolDirectory/otherlisted.txt"


def get_nasdaq_tickers():
    """ Generates a csv file containing symbols of companies trading on the NASDAQ exchange. """

    # read csv file into a df
    df = pd.read_csv(NASDAQ_URL, sep="|")

    # get the symbols
    tickers_column = df[["Symbol"]]

    # save to csv file
    save_path = os.path.join(BASE_PATH, "nasdaq.csv")
    tickers_column.to_csv(save_path, index=False, header="Symbol")


def get_nyse_tickers():
    """ Generates a csv file containing symbols of companies trading on the NYSE exchange. """

    # read csv file into a df
    df = pd.read_csv(OTHER_URL, sep="|")

    # filter rows, selecting only those traded on NYSE
    nyse_df = df[df["Exchange"] == "N"]

    # rename column, refactor df
    nyse_df = nyse_df.rename(columns={"ACT Symbol": "Symbol"})
    tickers_column = nyse_df[["Symbol"]]

    # save to csv file
    save_path = os.path.join(BASE_PATH, "nyse.csv")
    tickers_column.to_csv(save_path, index=False, header="Symbol")


def get_amex_tickers():
    """ Generates a csv file containing symbols of companies trading on the AMEX exchange. """

    # read csv file into a df
    df = pd.read_csv(OTHER_URL, sep="|")

    # filter rows, selecting only those traded on AMEX
    amex_df = df[df["Exchange"] == "A"]

    # rename column, refactor df
    amex_df = amex_df.rename(columns={"ACT Symbol": "Symbol"})
    tickers_column = amex_df[["Symbol"]]

    # save to csv file
    save_path = os.path.join(BASE_PATH, "amex.csv")
    tickers_column.to_csv(save_path, index=False, header="Symbol")


def load_nasdaq_tickers():
    """ Loads the symbols from the nasdaq.csv file into a pandas DF and returns as a list. """

    # get file path
    nasdaq_path = os.path.join(DATA_PATH, "nasdaq.csv")

    # refactor into a df with column, return as list
    df = pd.read_csv(nasdaq_path)

    # return df as a list
    return df["Symbol"].tolist()


def load_nyse_tickers():
    """ Loads the symbols from the nyse.csv file into a pandas DF and returns as a list. """

    # get file path
    nyse_path = os.path.join(DATA_PATH, "nyse.csv")

    # refactor into a df with column, return as list
    df = pd.read_csv(nyse_path)

    # return df as a list
    return df["Symbol"].tolist()


def load_amex_tickers():
    """ Loads the symbols from the amex.csv file into a pandas DF and returns as a list. """

    # get file path
    amex_path = os.path.join(DATA_PATH, "amex.csv")

    # read csv file into df
    df = pd.read_csv(amex_path)
    
    # return df as a list
    return df["Symbol"].tolist()


def get_all_symbols():
    """ Loads the symbols of companies traded on the NASDAQ, NYSE AND AMEX and returns
        them as a set. """

    nasdaq = set(load_nasdaq_tickers())
    nyse = set(load_nyse_tickers())
    amex = set(load_amex_tickers())

    return nasdaq | nyse | amex


ALL_SYMBOLS = get_all_symbols()
