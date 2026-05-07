import control as ct
import matplotlib.pyplot as plt

# RC de exemplo — ajuste R e C se quiser
R = 1.0  # Ohm (exemplo)
C = 1.0  # Farad (exemplo)

print(f"Parâmetros assumidos: R = {R} Ohm, C = {C} Farad")
print(f"Constante de tempo (tau = RC): {R * C} segundos")

# G(s) = 1 / (RCs + 1)
num = [1]
den = [R * C, 1]

G = ct.tf(num, den)
print("\nFunção de Transferência G(s):")
print(G)

polos = ct.poles(G)
zeros = ct.zeros(G)
print("\nPólos do sistema:", polos)
print("Zeros do sistema:", zeros)

plt.figure(figsize=(12, 6))

plt.subplot(1, 2, 1)
ct.pzmap(G, plot=True, grid=True)
plt.title("Diagrama de Polos e Zeros de G(s)")
plt.xlabel("Eixo Real")
plt.ylabel("Eixo Imaginário")
plt.grid(True)

plt.subplot(1, 2, 2)
T, yout = ct.step_response(G)
plt.plot(T, yout, label="Resposta ao Degrau")
plt.title("Resposta ao Degrau de G(s)")
plt.xlabel("Tempo (s)")
plt.ylabel("Amplitude")
plt.grid(True)
plt.legend()

plt.tight_layout()
plt.show()