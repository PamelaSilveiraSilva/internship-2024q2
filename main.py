from solution.solution import SelicCalc
from datetime import date

if __name__ == '__main__':
    # Instancia a classe SelicCalc
    calc = SelicCalc()

    # Calcula e obtém o DataFrame com os resultados
    df = calc.calc_amount(
        start_date=date(2010, 1, 1),
        end_date=date(2021, 3, 1),
        capital=657.43,
        frequency="daily",
        save_csv=False,
    )
    