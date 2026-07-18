from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List
from abc import ABC, abstractmethod


SIGMA = 5.670374419e-8

@dataclass
class MissionRequirements:
    orbit_altitude_km: float = 600.0
    mission_duration_years: float = 5.0
    eclipse_duration_min: float = 35.0

@dataclass
class ThermalRequirements:
    operational_min_temp_C: float = -10.0
    operational_max_temp_C: float = 40.0
    survival_min_temp_C: float = -20.0
    survival_max_temp_C: float = 60.0
    heater_power_limit_W: float = 100.0

@dataclass
class Subsystem(ABC):
    name: str
    dissipated_power_W: float

    def analyze(self) -> None:
        pass

@dataclass
class PowerSubsystem(Subsystem):
    available_power_W: float = 500.0
    def analyze(self) -> None:
        print(f"[Power] Available Power = {self.available_power_W:.1f} W")

@dataclass
class ADCSSubsystem(Subsystem):
    pointing_mode: str = "Nadir"
    def analyze(self) -> None:
        print(f"[ADCS] Pointing Mode = {self.pointing_mode}")

@dataclass
class StructureSubsystem(Subsystem):
    material: str = "Aluminum"
    def analyze(self) -> None:
        print(f"[Structure] Material = {self.material}")

@dataclass
class PayloadSubsystem(Subsystem):
    payload_type: str = "Camera"
    def analyze(self) -> None:
        print(f"[Payload] Type = {self.payload_type}")

@dataclass
class ThermalAnalyzer:
    total_dissipated_power_W: float
    radiator_emissivity: float = 0.85
    radiator_temperature_C: float = 20.0

    def radiator_area(self) -> float:
        T = self.radiator_temperature_C + 273.15
        return self.total_dissipated_power_W / (self.radiator_emissivity * SIGMA * T**4)

    def heater_power(self, expected_temp_C: float, required_temp_C: float) -> float:
        if expected_temp_C >= required_temp_C:
            return 0.0
        return 5.0 * (required_temp_C - expected_temp_C)

@dataclass
class ThermalSubsystem(Subsystem):
    requirements: ThermalRequirements
    radiator_emissivity: float = 0.85
    estimated_cold_case_temp_C: float = -25.0
    required_radiator_area_m2: float = 0.0
    required_heater_power_W: float = 0.0

    def analyze(self) -> None:
        analyzer = ThermalAnalyzer(self.dissipated_power_W, self.radiator_emissivity)
        self.required_radiator_area_m2 = analyzer.radiator_area()
        self.required_heater_power_W = analyzer.heater_power(
            self.estimated_cold_case_temp_C, self.requirements.survival_min_temp_C
        )
        print(f"[Thermal] Radiator Area = {self.required_radiator_area_m2:.3f} m²")
        print(f"[Thermal] Heater Power = {self.required_heater_power_W:.2f} W")

@dataclass
class ArchitectureCandidate:
    name: str
    mass_score: float
    power_score: float
    reliability_score: float
    complexity_score: float

@dataclass
class TradeStudy:
    candidates: List[ArchitectureCandidate]
    weights: Dict[str, float] = field(default_factory=lambda: {"mass": 0.25, "power": 0.25, "reliability": 0.30, "complexity": 0.20})

    def evaluate(self):
        best = max(self.candidates, key=lambda c: 
            c.mass_score * self.weights["mass"] +
            c.power_score * self.weights["power"] +
            c.reliability_score * self.weights["reliability"] +
            c.complexity_score * self.weights["complexity"])
        for c in self.candidates:
            score = (c.mass_score * self.weights["mass"] + c.power_score * self.weights["power"] +
                     c.reliability_score * self.weights["reliability"] + c.complexity_score * self.weights["complexity"])
            print(f"{c.name} Score = {score:.3f}")
        return best

@dataclass
class VerificationModule:
    thermal: ThermalSubsystem
    def verify(self):
        ok = self.thermal.required_heater_power_W <= self.thermal.requirements.heater_power_limit_W
        print("[Verification] PASS" if ok else "[Verification] FAIL")
        return ok

@dataclass
class DesignIteration:
    max_iterations: int = 10
    def run(self, thermal):
        for i in range(self.max_iterations):
            thermal.analyze()
            if thermal.required_heater_power_W <= thermal.requirements.heater_power_limit_W:
                print(f"[Iteration] Converged at iteration {i+1}")
                break
            thermal.radiator_emissivity += 0.01

@dataclass
class Satellite:
    name: str
    mission: MissionRequirements
    subsystems: Dict[str, Subsystem] = field(default_factory=dict)

    def add_subsystem(self, s):
        self.subsystems[s.name] = s

    def analyze(self):
        print(f"\n===== Satellite: {self.name} =====\n")
        for s in self.subsystems.values():
            s.analyze()

if __name__ == "__main__":
    print("🚀 Starting Satellite Conceptual Design Analysis...\n")
    mission = MissionRequirements()
    thermal_req = ThermalRequirements()

    power = PowerSubsystem(name="Power", dissipated_power_W=20, available_power_W=600)
    adcs = ADCSSubsystem(name="ADCS", dissipated_power_W=30)
    payload = PayloadSubsystem(name="Payload", dissipated_power_W=120)
    structure = StructureSubsystem(name="Structure", dissipated_power_W=10)

    total_heat = 20 + 30 + 120 + 10
    thermal = ThermalSubsystem(name="Thermal", dissipated_power_W=total_heat, requirements=thermal_req)

    sat = Satellite(name="ConceptSat", mission=mission)
    for s in [power, adcs, payload, structure, thermal]:
        sat.add_subsystem(s)

    sat.analyze()

    print("\n===== Trade Study =====\n")
    study = TradeStudy(candidates=[
        ArchitectureCandidate("Passive", 9, 10, 8, 10),
        ArchitectureCandidate("Passive+Heater", 8, 8, 10, 8),
        ArchitectureCandidate("Active Loop", 5, 4, 9, 3),
    ])
    best = study.evaluate()
    print(f"\nSelected Architecture = {best.name}")

    print("\n===== Design Iteration =====\n")
    DesignIteration().run(thermal)

    print("\n===== Verification =====\n")
    VerificationModule(thermal).verify()

    print("\n✅ Analysis completed successfully!")
