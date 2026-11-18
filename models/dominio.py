from typing import List, Any

"""
@author Armando Imanol Aguilar Espiricueto
"""

class ObjetivoNutricional:
    def __init__(self, caloriasMeta: float, proteinaMeta: float):
        self.caloriasMeta = caloriasMeta
        self.proteinaMeta = proteinaMeta

    def EstaCumplido(self, valorCalorias: float, valorProteina: float = 0.0) -> bool:
        return valorCalorias <= self.caloriasMeta and valorProteina >= self.proteinaMeta

class Recomendacion:
    def AvisoLegal(self) -> str:
        # Requisito explícito del negocio: no sustituye atención médica
        return "Las recomendaciones son informativas y no sustituyen la atención de un nutriólogo."

class ComparadorHabitos:
    def Comparar(self, registros: List[Any], objetivo: ObjetivoNutricional) -> str:
        total_calorias = round(sum(r.componente.GetCalorias() for r in registros), 1)
        total_proteina = round(sum(r.componente.GetNutrientes().proteina for r in registros), 1)
        meta_calorias = round(objetivo.caloriasMeta, 1)
        meta_proteina = round(objetivo.proteinaMeta, 1)

        if objetivo.EstaCumplido(total_calorias, total_proteina):
            return (
                f"Objetivo cumplido: {total_calorias:.1f}/{meta_calorias:.1f} kcal y "
                f"{total_proteina:.1f}/{meta_proteina:.1f}g de proteína."
            )
        return (
            f"En progreso o fuera de rango: llevas {total_calorias:.1f}/{meta_calorias:.1f} kcal y "
            f"{total_proteina:.1f}/{meta_proteina:.1f}g de proteína."
        )

    def ObtenerTendencias(self, registros: List[Any]) -> str:
        if not registros:
            return "Sin tendencia aún: registra tus primeras comidas del día."

        proteina = round(sum(r.componente.GetNutrientes().proteina for r in registros), 1)
        carbos = round(sum(r.componente.GetNutrientes().carbohidratos for r in registros), 1)
        grasas = round(sum(r.componente.GetNutrientes().grasas for r in registros), 1)

        macros = {
            "proteínas": proteina,
            "carbohidratos": carbos,
            "grasas": grasas,
        }
        macro_dominante = max(macros, key=macros.get)
        valor_dominante = macros[macro_dominante]

        if valor_dominante == 0:
            return "Tendencia: Consumo bajo en macronutrientes principales."

        return (
            f"Tendencia de consumo: predomina el aporte de {macro_dominante} "
            f"({valor_dominante:.1f}g acumulados en {len(registros)} registro(s))."
        )