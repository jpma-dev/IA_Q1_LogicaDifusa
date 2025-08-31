import tkinter as tk
from tkinter import messagebox, ttk

import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl

import clips

import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# -------------------------
# 1) DEFINICIÓN SCikit-Fuzzy
# -------------------------
# Universos
presupuesto = ctrl.Antecedent(np.arange(5, 81, 1), 'presupuesto')    # millones COP
experiencia = ctrl.Antecedent(np.arange(0, 37, 1), 'experiencia')    # meses
cilindraje = ctrl.Consequent(np.arange(100, 1201, 1), 'cilindraje')  # cc

# Funciones de membresía (trapezoidales)
presupuesto['bajo'] = fuzz.trapmf(presupuesto.universe, [5, 5, 15, 20])
presupuesto['medio'] = fuzz.trapmf(presupuesto.universe, [15, 20, 45, 50])
presupuesto['alto'] = fuzz.trapmf(presupuesto.universe, [45, 50, 80, 80])

experiencia['principiante'] = fuzz.trapmf(experiencia.universe, [0, 0, 6, 8])
experiencia['promedio'] = fuzz.trapmf(experiencia.universe, [6, 8, 18, 20])
experiencia['avanzado'] = fuzz.trapmf(experiencia.universe, [18, 20, 36, 36])

cilindraje['bajo']  = fuzz.trapmf(cilindraje.universe, [100, 100, 200, 350])
cilindraje['medio'] = fuzz.trapmf(cilindraje.universe, [300, 450, 600, 750])
cilindraje['alto']  = fuzz.trapmf(cilindraje.universe, [700, 900, 1200, 1200])

# Reglas scikit-fuzzy (para control numérico)
rule1 = ctrl.Rule(presupuesto['bajo'] & experiencia['principiante'], cilindraje['bajo'])
rule2 = ctrl.Rule(presupuesto['bajo'] & experiencia['promedio'], cilindraje['bajo'])
rule3 = ctrl.Rule(presupuesto['bajo'] & experiencia['avanzado'], cilindraje['bajo'])

rule4 = ctrl.Rule(presupuesto['medio'] & experiencia['principiante'], cilindraje['bajo'])
rule5 = ctrl.Rule(presupuesto['medio'] & experiencia['promedio'], cilindraje['medio'])
rule6 = ctrl.Rule(presupuesto['medio'] & experiencia['avanzado'], cilindraje['medio'])

rule7 = ctrl.Rule(presupuesto['alto'] & experiencia['principiante'], cilindraje['medio'])
rule8 = ctrl.Rule(presupuesto['alto'] & experiencia['promedio'], cilindraje['alto'])
rule9 = ctrl.Rule(presupuesto['alto'] & experiencia['avanzado'], cilindraje['alto'])

cilindraje_ctrl = ctrl.ControlSystem([rule1, rule2, rule3, rule4, rule5, rule6, rule7, rule8, rule9])
cilindraje_sim = ctrl.ControlSystemSimulation(cilindraje_ctrl)

# -------------------------
# 2) ENV CLIPSPy PARA REGISTRAR REGLAS ACTIVADAS
# -------------------------
clips_env = clips.Environment()
# Plantilla para almacenar activación de reglas
clips_env.build("""
(deftemplate regla-activada
    (slot nombre)
    (slot fuerza)
    (slot antecedente1)
    (slot antecedente2))
""")

# Regla por defecto
clips_env.build("""
(defrule regla-default
    (not (regla-activada (nombre ?n)))
=>
    (assert (regla-activada (nombre "DEFAULT") 
                            (fuerza 0) 
                            (antecedente1 "N/A") 
                            (antecedente2 "N/A"))))
""")

clips_env.reset()

# -------------------------
# 3) FUNCIÓN AUXILIAR: EVALUAR MEMBRESÍAS Y ACTIVAR REGLAS EN CLIPS
# -------------------------
def evaluar_y_registrar_clips(p_val, e_val):
    activated = []

    clips_env.reset()

    g_pres_bajo = fuzz.interp_membership(presupuesto.universe, presupuesto['bajo'].mf, p_val)
    g_pres_medio = fuzz.interp_membership(presupuesto.universe, presupuesto['medio'].mf, p_val)
    g_pres_alto = fuzz.interp_membership(presupuesto.universe, presupuesto['alto'].mf, p_val)

    g_exp_princ = fuzz.interp_membership(experiencia.universe, experiencia['principiante'].mf, e_val)
    g_exp_prom = fuzz.interp_membership(experiencia.universe, experiencia['promedio'].mf, e_val)
    g_exp_avanz = fuzz.interp_membership(experiencia.universe, experiencia['avanzado'].mf, e_val)

    pres_map = {'bajo': float(g_pres_bajo), 'medio': float(g_pres_medio), 'alto': float(g_pres_alto)}
    exp_map = {'principiante': float(g_exp_princ), 'promedio': float(g_exp_prom), 'avanzado': float(g_exp_avanz)}

    f_R1 = min(pres_map['bajo'], exp_map['principiante'])
    if f_R1 > 0:
        clips_env.assert_string(f"(regla-activada (nombre R1) (fuerza {f_R1}) "
                                f"(antecedente1 presupuesto=bajo) (antecedente2 experiencia=principiante))")
        activated.append({'rule': 'R1', 'fuerza': f_R1, 'consequente': 'bajo'})

    f_R2 = min(pres_map['bajo'], exp_map['promedio'])
    if f_R2 > 0:
        clips_env.assert_string(f"(regla-activada (nombre R2) (fuerza {f_R2}) "
                                f"(antecedente1 presupuesto=bajo) (antecedente2 experiencia=promedio))")
        activated.append({'rule': 'R2', 'fuerza': f_R2, 'consequente': 'bajo'})

    f_R3 = min(pres_map['bajo'], exp_map['avanzado'])
    if f_R3 > 0:
        clips_env.assert_string(f"(regla-activada (nombre R3) (fuerza {f_R3}) "
                                f"(antecedente1 presupuesto=bajo) (antecedente2 experiencia=avanzado))")
        activated.append({'rule': 'R3', 'fuerza': f_R3, 'consequente': 'bajo'})

    f_R4 = min(pres_map['medio'], exp_map['principiante'])
    if f_R4 > 0:
        clips_env.assert_string(f"(regla-activada (nombre R4) (fuerza {f_R4}) "
                                f"(antecedente1 presupuesto=medio) (antecedente2 experiencia=principiante))")
        activated.append({'rule': 'R4', 'fuerza': f_R4, 'consequente': 'bajo'})

    f_R5 = min(pres_map['medio'], exp_map['promedio'])
    if f_R5 > 0:
        clips_env.assert_string(f"(regla-activada (nombre R5) (fuerza {f_R5}) "
                                f"(antecedente1 presupuesto=medio) (antecedente2 experiencia=promedio))")
        activated.append({'rule': 'R5', 'fuerza': f_R5, 'consequente': 'medio'})

    f_R6 = min(pres_map['medio'], exp_map['avanzado'])
    if f_R6 > 0:
        clips_env.assert_string(f"(regla-activada (nombre R6) (fuerza {f_R6}) "
                                f"(antecedente1 presupuesto=medio) (antecedente2 experiencia=avanzado))")
        activated.append({'rule': 'R6', 'fuerza': f_R6, 'consequente': 'medio'})

    f_R7 = min(pres_map['alto'], exp_map['principiante'])
    if f_R7 > 0:
        clips_env.assert_string(f"(regla-activada (nombre R7) (fuerza {f_R7}) "
                                f"(antecedente1 presupuesto=alto) (antecedente2 experiencia=principiante))")
        activated.append({'rule': 'R7', 'fuerza': f_R7, 'consequente': 'medio'})

    f_R8 = min(pres_map['alto'], exp_map['promedio'])
    if f_R8 > 0:
        clips_env.assert_string(f"(regla-activada (nombre R8) (fuerza {f_R8}) "
                                f"(antecedente1 presupuesto=alto) (antecedente2 experiencia=promedio))")
        activated.append({'rule': 'R8', 'fuerza': f_R8, 'consequente': 'alto'})

    f_R9 = min(pres_map['alto'], exp_map['avanzado'])
    if f_R9 > 0:
        clips_env.assert_string(f"(regla-activada (nombre R9) (fuerza {f_R9}) "
                                f"(antecedente1 presupuesto=alto) (antecedente2 experiencia=avanzado))")
        activated.append({'rule': 'R9', 'fuerza': f_R9, 'consequente': 'alto'})

    if not activated:
        clips_env.assert_string(
            '(regla-activada (nombre DEFAULT) (fuerza 0) '
            '(antecedente1 "N/A") (antecedente2 "N/A"))'
        )
        activated.append({'rule': 'DEFAULT', 'fuerza': 0, 'consequente': 'N/A'})

    clips_env.run()
    return activated

# -------------------------
# 4) FUNCIONALIDAD PRINCIPAL: COMPUTO Y GRAFICADO EMBEBIDO
# -------------------------
def calcular_y_mostrar():
    try:
        p_val = presupuesto_var.get()
        e_val = experiencia_var.get()

        if not (5 <= p_val <= 80):
            messagebox.showwarning("Rango presupuesto", "Presupuesto debe estar entre 5 y 80 (millones COP).")
            return
        if not (0 <= e_val <= 36):
            messagebox.showwarning("Rango experiencia", "Experiencia debe estar entre 0 y 36 meses.")
            return

        cilindraje_sim.input['presupuesto'] = p_val
        cilindraje_sim.input['experiencia'] = e_val
        cilindraje_sim.compute()

        if 'cilindraje' in cilindraje_sim.output:
            resultado = cilindraje_sim.output['cilindraje']
            label_result.config(text=f"{resultado:.2f} cc")
        else:
            resultado = None
            label_result.config(text="Sin recomendación")

        activated = evaluar_y_registrar_clips(p_val, e_val)

        listbox_reglas.delete(0, tk.END)
        if activated:
            for a in activated:
                listbox_reglas.insert(tk.END, f"{a['rule']} (fuerza={a['fuerza']:.3f}) -> cilindraje {a['consequente']}")
        else:
            listbox_reglas.insert(tk.END, "⚠️ Ninguna regla específica. Se activó regla-default.")

        # Gráficas
        fig.clear()
        ax1 = fig.add_subplot(3,1,1)
        ax1.plot(presupuesto.universe, presupuesto['bajo'].mf, '--', label='bajo')
        ax1.plot(presupuesto.universe, presupuesto['medio'].mf, '-.', label='medio')
        ax1.plot(presupuesto.universe, presupuesto['alto'].mf, '-', label='alto')
        ax1.axvline(p_val, color='k', linewidth=1, alpha=0.7)
        ax1.set_title('Presupuesto (M $COP)')
        ax1.legend()

        ax2 = fig.add_subplot(3,1,2)
        ax2.plot(experiencia.universe, experiencia['principiante'].mf, '--', label='principiante')
        ax2.plot(experiencia.universe, experiencia['promedio'].mf, '-.', label='promedio')
        ax2.plot(experiencia.universe, experiencia['avanzado'].mf, '-', label='avanzado')
        ax2.axvline(e_val, color='k', linewidth=1, alpha=0.7)
        ax2.set_title('Experiencia (meses)')
        ax2.legend()

        ax3 = fig.add_subplot(3,1,3)
        ax3.plot(cilindraje.universe, cilindraje['bajo'].mf, '--', label='bajo')
        ax3.plot(cilindraje.universe, cilindraje['medio'].mf, '-.', label='medio')
        ax3.plot(cilindraje.universe, cilindraje['alto'].mf, '-', label='alto')
        ax3.axvline(resultado, color='r', linewidth=2, label=f'Resultado: {resultado:.1f} cc')
        ax3.set_title('Cilindraje recomendado (cc)')
        ax3.legend()

        fig.tight_layout(pad=2.0)

        canvas.draw()

    except Exception as ex:
        messagebox.showerror("Error", f"Ocurrió un error: {ex}")

# -------------------------
# 5) INTERFAZ TKINTER
# -------------------------
root = tk.Tk()
root.title("Sistema Difuso - Cilindraje Recomendado")
root.geometry("900x900")

frm_inputs = ttk.Frame(root, padding=10)
frm_inputs.pack(side=tk.TOP, fill=tk.X)

ttk.Label(frm_inputs, text="Presupuesto (millones COP):").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
presupuesto_var = tk.DoubleVar()
slider_presupuesto = tk.Scale(frm_inputs, from_=5, to=80, orient="horizontal", variable=presupuesto_var, resolution=1, length=200)
slider_presupuesto.grid(row=0, column=1, padx=5, pady=5)
label_presu_val = ttk.Label(frm_inputs, textvariable=presupuesto_var)
label_presu_val.grid(row=0, column=2, padx=5)

ttk.Label(frm_inputs, text="Experiencia (meses):").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
experiencia_var = tk.DoubleVar()
slider_experiencia = tk.Scale(frm_inputs, from_=0, to=36, orient="horizontal", variable=experiencia_var, resolution=1, length=200)
slider_experiencia.grid(row=1, column=1, padx=5, pady=5)
label_exp_val = ttk.Label(frm_inputs, textvariable=experiencia_var)
label_exp_val.grid(row=1, column=2, padx=5)

btn_calcular = ttk.Button(frm_inputs, text="Calcular", command=calcular_y_mostrar)
btn_calcular.grid(row=0, column=2, rowspan=2, columnspan=2, padx=100)

frm_result = ttk.Frame(root, padding=10)
frm_result.pack(side=tk.TOP, fill=tk.X)
ttk.Label(frm_result, text="Cilindraje recomendado:").grid(row=0, column=0, sticky=tk.W)
label_result = ttk.Label(frm_result, text=" (cc)", font=("Helvetica", 14, "bold"))
label_result.grid(row=0, column=1, sticky=tk.W, padx=10)

frm_rules = ttk.Frame(root, padding=10)
frm_rules.pack(side=tk.TOP, fill=tk.X)
ttk.Label(frm_rules, text="Reglas activadas").pack(anchor=tk.W)
listbox_reglas = tk.Listbox(frm_rules, height=4, bd=0)
listbox_reglas.pack(fill=tk.X, padx=2, pady=2)

fig = plt.Figure(figsize=(8, 6), dpi=100)
canvas = FigureCanvasTkAgg(fig, master=root)
canvas_widget = canvas.get_tk_widget()
canvas_widget.pack(side=tk.TOP, fill=tk.BOTH, expand=1)

root.mainloop()
