# derivation-006: APD Hardware Sizing

## 1. Topology Definition

### APD H-Bridge Configuration

```
DC-link (Vdc) ──┬── [SW1] ──┬── [L_apd] ──┬── [SW3] ──┬── GND
                │            │              │            │
                └── [SW2] ──┘              └── [SW4] ──┘
                                         │
                                    [Capd] ── GND
                                    (Vapd)
```

- **Topology**: Bidirectional buck-boost with inductor on capacitor side
- **Inductor position**: Capacitor-side (between H-bridge midpoints and Capd)
- **PWM mode**: Unipolar switching (lower losses than bipolar)
- **Current sensing**: Inductor current (i_L)
- **Voltage stress**: Case A — max(Vdc, Vapd) per switch (not Vdc+Vapd)
  - With unipolar switching, each switch sees max(Vdc, Vapd), not the sum
  - Vds_max = max(400V, 450V) = 450V → **650V MOSFET sufficient**

### Voltage Window

| Parameter | Value | Notes |
|-----------|-------|-------|
| Vapd_min | 250V | Minimum APD voltage |
| Vapd_max | 450V | Maximum APD voltage |
| Vapd_center | 364V | Energy center: √((250²+450²)/2) |
| Vdc_nom | 300V | Nominal DC-link |
| Vdc_max | 400V | High-line worst case |

---

## 2. APD Power and Low-Frequency Current

### Peak APD Power

```
P_apd_peak = D × Pavg
```

| D | P_apd_peak |
|---|-----------|
| 0.90 | 270W |
| 0.95 | 285W |

### Low-Frequency Current (100Hz)

**Peak current** (conservative, at Vapd_min):

```
I_apd_peak ≈ P_apd_peak / Vapd_min
```

| D | I_apd_peak |
|---|-----------|
| 0.90 | 270/250 = 1.08A |
| 0.95 | 285/250 = 1.14A |

**RMS current** (at Vapd_center):

```
I_apd_lf_rms ≈ P_apd_peak / (√2 × Vapd_center)
```

| D | I_apd_lf_rms |
|---|-------------|
| 0.90 | 270/(1.414×364) ≈ 0.52A |
| 0.95 | 285/(1.414×364) ≈ 0.55A |

**Conservative upper bound** (at Vapd_min):

| D | I_apd_lf_rms_upper |
|---|-------------------|
| 0.95 | 285/(1.414×250) ≈ 0.81A |

---

## 3. APD Inductor Sizing

### Formula

```
L_apd ≥ V_L,max / (2 × ΔI_L,pp × f_sw)
```

Where:
- V_L,max = max voltage across inductor during switching
- ΔI_L,pp = peak-to-peak ripple current
- f_sw = switching frequency

### Parameter Sweep

| f_sw (kHz) | ΔI_L,pp (A) | V_L,max=100V | V_L,max=200V | V_L,max=400V |
|------------|-------------|--------------|--------------|--------------|
| 20 | 0.3 | 8.3mH | 16.7mH | 33.3mH |
| 20 | 0.5 | 5.0mH | 10.0mH | 20.0mH |
| 20 | 0.8 | 3.1mH | 6.3mH | 12.5mH |
| 40 | 0.3 | 4.2mH | 8.3mH | 16.7mH |
| 40 | 0.5 | 2.5mH | 5.0mH | 10.0mH |
| 40 | 0.8 | 1.6mH | 3.1mH | 6.3mH |
| 60 | 0.3 | 2.8mH | 5.6mH | 11.1mH |
| 60 | 0.5 | 1.7mH | 3.3mH | 6.7mH |
| 60 | 0.8 | 1.0mH | 2.1mH | 4.2mH |

### Recommended Operating Point

For unipolar buck-boost with capacitor-side inductor:
- V_L,max ≈ max(Vdc, Vapd) - Vapd ≈ 100-150V (typical)
- f_sw = 40kHz (within F28035 capability)
- ΔI_L,pp = 0.4A (20-40% of I_apd_peak)

→ **L_apd ≈ 2.5–4.2mH**

First-pass recommendation: **L_apd = 3.3mH, Isat ≥ 3A**

---

## 4. Inductor RMS and Peak Current

### Combined Current

```
i_L(t) = i_lf(t) + i_ripple(t)
```

**RMS**:

```
I_L_rms² ≈ I_lf_rms² + ΔI_L,pp² / 12
```

**Peak**:

```
I_L_peak ≈ I_lf_peak + ΔI_L,pp / 2
```

### Numerical Example (D=0.95, ΔI_pp=0.5A)

```
I_lf_rms = 0.55A
I_ripple_rms = 0.5 / √12 = 0.144A
I_L_rms = √(0.55² + 0.144²) = 0.57A

I_lf_peak = 1.14A
I_L_peak = 1.14 + 0.25 = 1.39A
```

### Inductor Requirements

| Parameter | Requirement |
|-----------|------------|
| Inductance | 3.3mH (nominal) |
| Saturation current | ≥ 3.0A |
| RMS current | ≥ 1.0A |
| Core loss | Low at 40kHz (ferrite or sendust) |

---

## 5. APD Capacitor RMS Current

### Low-Frequency Component

```
I_C_lf_rms ≈ P_apd_peak / (√2 × Vapd_center) ≈ 0.55A
```

### High-Frequency Ripple Component

```
I_C_ripple_rms ≈ k_ripple × ΔI_L_pp / √12
```

Where k_ripple = 0.5–1.0 (depends on current sharing path).

For k_ripple = 0.5:

```
I_C_ripple_rms = 0.5 × 0.5 / 3.464 = 0.072A
```

### Total Capacitor RMS Current

```
I_C_rms = √(I_C_lf_rms² + I_C_ripple_rms²)
        = √(0.55² + 0.072²)
        ≈ 0.55A
```

### Capacitor Requirements

```yaml
Capd_requirements:
  capacitance: 16-22uF
  voltage_rating: >=500V (with margin for 450V max)
  low_frequency_rms_current: >=1A
  high_frequency_ripple_current: >=0.5A
  low_ESR: required (film capacitor)
  temperature_rating: 105°C preferred
  type: polypropylene film
```

---

## 6. MOSFET Voltage Rating

### Stress Analysis

**Case A — Unipolar switching (selected topology)**:
```
Vds_stress = max(Vdc_max, Vapd_max) = max(400V, 450V) = 450V
```

**Case B — Bipolar switching (not selected)**:
```
Vds_stress = Vdc_max + Vapd_max = 400V + 450V = 850V
```

### Selection

With unipolar switching: **650V MOSFET sufficient**

Recommended: 650V / 5A / Rds_on < 1Ω (e.g., IPW65R045C7 or similar)

---

## 7. MOSFET Current Rating

### Steady-State

```
I_L_peak ≈ 1.2–1.6A (from Section 4)
```

### Design Margins

| Factor | Multiplier | Rationale |
|--------|-----------|-----------|
| Inductor ripple | 1.0× | Already included |
| Transient overshoot | 1.5× | Startup, load step |
| Control overshoot | 1.3× | PI settling |
| Protection delay | 1.5× | OC trip time |
| **Total margin** | **~3×** | **Conservative** |

### Requirements

| Parameter | Requirement |
|-----------|------------|
| Continuous current (Id) | ≥ 5A |
| Peak pulse current | ≥ 10A |
| Rds_on | < 1Ω (for low conduction loss) |

---

## 8. MOSFET Loss Estimation

### Conduction Loss

```
P_cond ≈ I_rms² × Rds_on × duty_cycle
```

For I_rms = 0.57A, Rds_on = 0.45Ω, duty ≈ 0.5:

```
P_cond ≈ 0.57² × 0.45 × 0.5 = 0.073W per FET
Total (4 FETs): ≈ 0.29W
```

### Switching Loss

```
P_sw ≈ 0.5 × Vds × I_sw × (tr + tf) × f_sw
```

For Vds = 400V, I_sw = 1.5A, tr=tf=30ns, f_sw=40kHz:

```
P_sw ≈ 0.5 × 400 × 1.5 × 60e-9 × 40e3 = 0.72W per FET
Total (4 FETs): ≈ 2.88W
```

### Total APD Loss

```
P_apd_total ≈ P_cond + P_sw ≈ 0.29 + 2.88 = 3.17W
```

This is ~1% of 300W — consistent with derivation-005's Ploss_frac = 3%.

---

## 9. Deadtime Requirements

### Voltage Error from Deadtime

```
V_error_fraction ≈ 2 × t_dead × f_sw
```

| t_dead | f_sw=40kHz | V_error |
|--------|-----------|---------|
| 200ns | 1.6% | Acceptable |
| 300ns | 2.4% | Marginal |
| 500ns | 4.0% | Too high |

### Recommendation

- **Deadtime**: 200–300ns
- **Requirement**: Deadtime compensation or power loop error absorption
- **Faster MOSFETs** (lower tr/tf) allow shorter deadtime

---

## 10. APD Control Bandwidth

### Requirement

APD must track 100Hz power pulsation. Minimum bandwidth:

```
f_bw_apd ≥ 3 × f_ripple = 3 × 100Hz = 300Hz
```

Recommended: **f_bw_apd ≥ 500Hz** (5× margin)

### Implementation

- APD PWM: 40kHz (hardware timer)
- APD control update: 10–20kHz (within ISR or separate timer)
- Voltage loop bandwidth: 500–1000Hz
- Current loop bandwidth: 2–5kHz

---

## 11. Summary: APD Hardware Bill of Materials

| Component | Specification | Notes |
|-----------|--------------|-------|
| L_apd | 3.3mH / 3A saturation / 1A RMS | Ferrite or sendust core |
| Capd | 22µF / 500V / ≥1A RMS | Polypropylene film, low ESR |
| MOSFETs (×4) | 650V / 5A / Rds_on < 1Ω | Fast switching (tr/tf < 30ns) |
| Gate driver | 4× half-bridge driver | With deadtime generation |
| f_sw | 40kHz | Within F28035 PWM capability |
| Deadtime | 200–300ns | With compensation |
| APD control bw | ≥500Hz | Voltage loop |

---

## 12. Key Risks and Limitations

1. **Topology voltage stress**: Case A (unipolar) assumed; must verify with actual schematic
2. **Inductor core loss**: Not modeled; depends on core material and frequency
3. **Capacitor ESR**: Not modeled; affects ripple and thermal
4. **Thermal design**: MOSFET and inductor cooling not addressed
5. **EMI**: High dv/dt switching not analyzed
6. **Startup inrush**: Pre-charge circuit not designed
7. **Protection coordination**: OC/OV/UVLO timing not detailed

---

## 13. Decision Record

**APD hardware is realizable** with standard components:
- 3.3mH inductor (manageable size for 300W)
- 22µF/500V film capacitor (standard part)
- 650V MOSFETs (widely available)
- Total APD loss ~3W (~1% of 300W)

**No showstopper** found for APD hardware implementation.
