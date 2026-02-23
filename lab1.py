import math
import matplotlib.pyplot as plt

stan = 123 # ziarno


def losuj():
    global stan
    # Wzór: (stała * stan + stała) % wielka_liczba
    stan = (1103515245 * stan + 12345) % 2147483648
    return stan / 2147483648


# 2. USTAWIENIA
ile = 5000
lam = 4
srednia = 10
odchylenie = 2

# 3. GENEROWANIE POISSONA
poisson_dane = []
L = math.exp(-lam)

for _ in range(ile):
    p = 1.0
    k = 0
    while p > L:
        p = p * losuj()
        k = k + 1
    poisson_dane.append(k - 1)

# 4. GENEROWANIE GAUSSA
gauss_dane = []
for _ in range(ile // 2):
    u1 = losuj()
    u2 = losuj()
    # Magiczny wzór Box-Muller
    pomocnicza = math.sqrt(-2.0 * math.log(u1))
    z0 = pomocnicza * math.cos(2.0 * math.pi * u2)
    z1 = pomocnicza * math.sin(2.0 * math.pi * u2)

    gauss_dane.append(z0 * odchylenie + srednia)
    gauss_dane.append(z1 * odchylenie + srednia)

# 5. WYKRESY
plt.subplot(2, 1, 1)
plt.hist(poisson_dane, bins=15, color='gold', edgecolor='black')
plt.title("Poisson")

plt.subplot(2, 1, 2)
plt.hist(gauss_dane, bins=50, color='tomato', edgecolor='black')
plt.title("Gauss")

plt.tight_layout()
plt.show()