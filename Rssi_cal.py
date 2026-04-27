import numpy as np
from scipy.optimize import minimize


enum PathLossModel:
    free_space = 2,
    room = 3,
    wall = 4

esp_values = [{TxPower: 10, n = PathLossModel.free_space},{TxPower: 10, n = PathLossModel.free_space},{TxPower: 10, n = PathLossModel.free_space}]


def update_esp_values(tx_power: float, path_loss_exponent: int, index: int):
    esp_values[index]['TxPower'] = tx_power
    esp_values[index]['n'] = path_loss_exponent

def add_esp():
    esp_values.append({'TxPower': 10, 'n': PathLossModel.free_space})

def rssi_to_meters(rssi : float, esp) -> float:
    return 10**((rssi - esp.tx_power) / (esp.path_loss_exponent * 10))



def residuals(pos):
    return sum((np.linalg.norm(pos - a) - d)**2
               for a, d in zip(anchors, dists))


result = minimize(residuals, x0=[2.5, 2.0], method='Nelder-Mead')

