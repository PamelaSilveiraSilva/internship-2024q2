from solution.solution import SelicCalc
from datetime import date

if __name__ == '__main__':
    # Instancia a classe SelicCalc
    calc = SelicCalc()

    # Calcula e obtém o DataFrame com os resultados
    df = calc.calc_amount(
        start_date=date(2000, 1, 1),
        end_date=date(2022, 3, 31),
        capital=657.43,
        frequency="day",
        save_csv=False,
    )
    