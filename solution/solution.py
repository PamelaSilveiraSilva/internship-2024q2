import os
import requests
import glob
import pandas as pd
from datetime import datetime, date
from io import StringIO

class SelicCalc:
    def __init__(self):
        # Define o caminho absoluto para o diretório atual.
        self._PATH = os.path.abspath(os.getcwd())

    def earned(self, df: pd.DataFrame) -> pd.DataFrame:
        # Adiciona uma coluna que calcula o valor ganho baseado no capital inicial.
        df["Amount earned"] = df["compound"] - self.capital
        return df

    def reshape_df(self, df: pd.DataFrame, frequency: str) -> pd.DataFrame:
        # Configura a coluna "data" como o índice do DataFrame.
        df.set_index("data", inplace=True)
        
        # Agrupa os dados com base na frequência selecionada (mensal ou anual).
        if frequency == "month":
            df = df.groupby([df.index.year, df.index.month]).tail(1)
        elif frequency == "year":
            df = df.groupby([df.index.year]).tail(1)
        
        # Ordena o DataFrame pelo índice (data) e ajusta as colunas.
        df = df.sort_index()
        df = self.earned(df)
        df.drop(["valor"], axis="columns", inplace=True)
        df.rename(columns={"compound": "Capital"}, inplace=True)
        df.index.names = ["Date"]
        return df

    def is_valid_input(self, start_date: date, end_date: date, frequency: str) -> list:
        # Verifica se o capital é um número válido (int ou float).
        if not isinstance(self.capital, (float, int)):
            raise Exception("capital should be int or float")
        
        # Verifica se as datas são objetos de data válidos e se a data de início não é posterior à data de fim.
        if isinstance(start_date, (datetime, date)) and isinstance(end_date, (datetime, date)):
            if start_date >= end_date:
                raise Exception("start_date cannot be greater than end_date")
            # Converte as datas para strings no formato "dd/mm/yyyy".
            start_date_str = datetime.strftime(start_date, "%d/%m/%Y")
            end_date_str = datetime.strftime(end_date, "%d/%m/%Y")
            return [start_date_str, end_date_str]
        else:
            raise Exception("Inputs are in wrong format, should be date object")

    def save_csv(self, df: pd.DataFrame, file_name: str):
        # Verifica se o arquivo CSV já existe no diretório.
        files_present = glob.glob(file_name)
        if not files_present:
            # Salva o DataFrame em um arquivo CSV se o arquivo não existir.
            df.to_csv(file_name)
            print(f"Path to csv output: {self._PATH}/{file_name}")
        else:
            print("File already exists, ignoring")

    def calc_sum(self, start_date: date, end_date: date, df: pd.DataFrame) -> float:
        # Filtra o DataFrame para o intervalo de datas fornecido.
        _df = df[(df["data"] >= start_date) & (df["data"] <= end_date)]
        # Calcula o valor acumulado para o capital investido.
        _df["x"] = self.capital
        _df["x"] = _df["x"] * _df["valor"].shift().add(1).cumprod().fillna(1)
        val = _df.iloc[-1]["x"]
        return val

    def max_val_range(self, df: pd.DataFrame, range_of: int = 500):
        # Encontra o melhor intervalo para investir dentro do DataFrame.
        length = len(df) - range_of
        best_start = None
        best_end = None
        best_value = 0
        
        # Itera sobre todos os possíveis intervalos no DataFrame.
        for i in range(length):
            start = df.iloc[i]["data"]
            end = df.iloc[i + range_of - 1]["data"]
            value = self.calc_sum(start, end, df)
            # Atualiza o melhor intervalo se o valor acumulado for maior que o melhor registrado.
            if value > best_value:
                best_start = start
                best_end = end
                best_value = value
        
        # Imprime o intervalo de investimento ideal e o valor ganho.
        print(
            f"\nThe best day to invest is {best_start.date()}, with an amount earned of {best_value} after {range_of} "
            f"days ({best_start.date()} to {best_end.date()})"
        )

    def calc_amount(
        self,
        start_date: date,
        end_date: date,
        capital: float,
        frequency: str,
        save_csv: bool,
    ) -> pd.DataFrame:
        # Define o capital e valida a entrada.
        self.capital = capital
        start_date_str, end_date_str = self.is_valid_input(start_date, end_date, frequency)
        
        # Monta a URL para a API com o intervalo de datas.
        base_url = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.11/dados?formato=json&"
        date_range_str = f"dataInicial={start_date_str}&dataFinal={end_date_str}"
        url = base_url + date_range_str
        
        # Faz a solicitação para obter os dados da API.
        resp = requests.get(url)
        
        # Converte a resposta JSON para um DataFrame.
        df = pd.read_json(StringIO(resp.text))
        
        # Converte a coluna "data" para o formato de data e a coluna "valor" para valores numéricos.
        df["data"] = pd.to_datetime(df["data"], format="%d/%m/%Y")
        df["valor"] = pd.to_numeric(df["valor"])
        
        # Ordena o DataFrame e remove a primeira linha se a data não estiver dentro do intervalo desejado.
        df.sort_values(by=["data"], inplace=True)
        if df.iloc[0]["data"] < pd.to_datetime(start_date_str):
            df.drop(index=df.index[0], axis=0, inplace=True)
        
        # Converte a taxa de valor para porcentagem.
        df["valor"] = df["valor"] / 100
        
        # Encontra o melhor intervalo de investimento.
        self.max_val_range(df)
        
        # Faz uma cópia do DataFrame para referência bruta.
        df_raw = df.copy()
        
        # Calcula o valor composto acumulado.
        df["compound"] = capital
        df["compound"] = df["compound"] * df["valor"].shift().add(1).cumprod().fillna(1)
        
        # Ajusta o DataFrame para a frequência desejada.
        sol_df = self.reshape_df(df, frequency)
        
        # Salva os DataFrames em arquivos CSV se solicitado.
        if save_csv:
            self.save_csv(sol_df, file_name="solution.csv")
            self.save_csv(df_raw, file_name="df_raw.csv")
        
        return sol_df

    def run_example(self):
        # Executa um exemplo de cálculo e imprime o resultado.
        print("Running example")
        df = self.calc_amount(
            start_date=date(2010, 1, 11),
            end_date=date(2021, 3, 1),
            capital=657.43,
            frequency="daily",
            save_csv=False,
        )
        info = (
            "\nArgs:\n"
            "start_date=date(2010, 1, 11),\n"
            "end_date=date(2021, 3, 1),\n"
            "capital=657.43,\n"
            "frequency='daily',\n"
            "save_csv=False\n"
        )
        print(info, df)

    def compound_interest(self, df: pd.DataFrame) -> pd.DataFrame:
        # Calcula o valor composto acumulado para o DataFrame.
        df["compound"] = self.capital
        df["compound"] = df["compound"] * df["valor"].shift().add(1).cumprod().fillna(1)
        return df
