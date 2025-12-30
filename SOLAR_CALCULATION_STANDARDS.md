# Solar System Sizing - Scientific Standards & Improvements

## Current State Analysis
The existing calculator uses basic but valid solar engineering principles but lacks the precision needed for professional solar installations.

## Scientific Calculation Framework

### 1. **Load Analysis (IEEE 1562 Standard)**
```python
# Current Implementation (Simplified)
daily_consumption = monthly_consumption / 30

# Recommended Implementation (Load Profile Based)
def calculate_load_profile(monthly_kwh, usage_pattern):
    """
    Calculate hourly load profile using actual consumption patterns
    Based on IEC 61724 standard for PV system monitoring
    """
    base_load = monthly_kwh / (30 * 24)  # Average hourly
    
    # Apply usage multipliers by time of day
    load_profile = {
        'night': base_load * 0.6,      # 22:00 - 06:00 (40% reduction)
        'morning': base_load * 1.2,    # 06:00 - 10:00 (20% increase) 
        'day': base_load * 0.8,        # 10:00 - 16:00 (20% reduction)
        'evening': base_load * 1.4     # 16:00 - 22:00 (40% increase)
    }
    
    return load_profile
```

### 2. **Solar Resource Assessment (NASA SSE/NREL)**
```python
# Current Implementation (Basic City Data)
solar_hours = {'nairobi': 5.2, 'mombasa': 5.8}

# Recommended Implementation (Precise Geographic Data)
def get_solar_irradiance(latitude, longitude):
    """
    Use NASA Surface meteorology and Solar Energy (SSE) data
    or NREL's PVWatts API for precise solar resource assessment
    """
    return {
        'ghi_monthly': [4.5, 5.1, 5.8, 6.2, 5.9, 5.1, 4.8, 5.2, 5.6, 5.4, 4.9, 4.3],  # kWh/m²/day
        'temperature_avg': [19.7, 20.5, 21.3, 20.1, 18.9, 16.8, 15.8, 16.9, 19.1, 20.8, 19.7, 19.2],
        'wind_speed': 3.2  # m/s average
    }
```

### 3. **System Sizing (IEC 61836 Standard)**
```python
def calculate_system_capacity_professional(load_profile, solar_data, location_params):
    """
    Professional system sizing using IEC 61836 guidelines
    """
    # Step 1: Energy Balance Analysis
    daily_energy_need = sum(load_profile.values()) * 24
    
    # Step 2: Temperature Corrections (IEC 61215)
    temp_coefficient = -0.004  # %/°C for c-Si panels
    avg_cell_temp = location_params['ambient_temp'] + 30  # NOCT approximation
    temp_derating = 1 + (temp_coefficient * (avg_cell_temp - 25))
    
    # Step 3: System Losses (Real-world factors)
    system_losses = {
        'soiling': 0.02,           # 2% dust/dirt
        'shading': 0.03,           # 3% partial shading
        'mismatch': 0.02,          # 2% module mismatch
        'ohmic': 0.02,             # 2% wiring losses
        'inverter': 0.04,          # 4% inverter losses
        'transformer': 0.01,       # 1% transformer losses
        'availability': 0.003      # 0.3% system downtime
    }
    
    total_derating = 1 - sum(system_losses.values())
    combined_derating = temp_derating * total_derating
    
    # Step 4: Peak Sun Hours Calculation
    psh = solar_data['ghi_monthly'][month] / 1000  # Convert Wh/m² to kWh/m²
    
    # Step 5: Required System Capacity
    required_capacity = daily_energy_need / (psh * combined_derating)
    
    return {
        'capacity_kw': required_capacity,
        'derating_factors': system_losses,
        'total_derating': combined_derating,
        'expected_generation': required_capacity * psh * combined_derating * 30
    }
```

### 4. **Battery Sizing (IEC 61427 Standard)**
```python
def calculate_battery_capacity_professional(load_profile, autonomy_days=1.5):
    """
    Professional battery sizing for solar systems
    Based on IEC 61427 standards for renewable energy storage
    """
    # Critical load during night/cloudy periods
    critical_daily_load = calculate_critical_load(load_profile)
    
    # Battery bank sizing
    required_capacity = critical_daily_load * autonomy_days
    
    # Apply battery efficiency and DOD limits
    battery_efficiency = 0.85  # Round-trip efficiency
    max_dod = 0.8  # 80% maximum depth of discharge for longevity
    
    # Calculate usable vs nominal capacity
    nominal_capacity = required_capacity / (battery_efficiency * max_dod)
    
    return {
        'nominal_capacity_kwh': nominal_capacity,
        'usable_capacity_kwh': required_capacity,
        'autonomy_days': autonomy_days,
        'expected_cycles': calculate_cycle_life(max_dod)
    }
```

### 5. **Economic Analysis (LCOE - Levelized Cost of Energy)**
```python
def calculate_lcoe_professional(system_cost, energy_output, system_life=25):
    """
    Calculate Levelized Cost of Energy using NREL methodology
    """
    # Include all lifecycle costs
    costs = {
        'initial_investment': system_cost,
        'annual_om': system_cost * 0.015,  # 1.5% annual O&M
        'replacement_costs': {
            'inverter': {'year': 12, 'cost': system_cost * 0.15},
            'battery': {'year': 10, 'cost': system_cost * 0.25}
        }
    }
    
    # Apply degradation (0.5%/year for c-Si)
    annual_degradation = 0.005
    
    # Calculate NPV of costs and energy
    discount_rate = 0.08  # 8% real discount rate
    
    total_energy = 0
    total_costs = costs['initial_investment']
    
    for year in range(1, system_life + 1):
        # Energy with degradation
        annual_energy = energy_output * (1 - annual_degradation) ** year
        discounted_energy = annual_energy / (1 + discount_rate) ** year
        total_energy += discounted_energy
        
        # O&M costs
        discounted_om = costs['annual_om'] / (1 + discount_rate) ** year
        total_costs += discounted_om
        
        # Replacement costs
        for component, details in costs['replacement_costs'].items():
            if year == details['year']:
                discounted_replacement = details['cost'] / (1 + discount_rate) ** year
                total_costs += discounted_replacement
    
    lcoe = total_costs / total_energy  # KES/kWh
    
    return {
        'lcoe_kes_per_kwh': lcoe,
        'total_lifecycle_energy': total_energy,
        'total_lifecycle_costs': total_costs
    }
```

## Implementation Priority

### Phase 1: Immediate Improvements (Scientific Foundation)
1. **Enhanced Location Data**: Integrate NASA SSE or NREL databases
2. **Temperature Corrections**: Add cell temperature calculations
3. **System Loss Factors**: Include realistic derating factors
4. **Load Profile Analysis**: Account for daily usage patterns

### Phase 2: Professional Features
1. **Shading Analysis**: Basic roof orientation considerations  
2. **Component Optimization**: Size ratios (DC/AC, battery/load)
3. **Economic Optimization**: Find least-cost solution meeting energy needs
4. **Seasonal Variations**: Monthly energy balance calculations

### Phase 3: Advanced Features
1. **3D Shading Analysis**: Import roof models
2. **Weather Data Integration**: Real-time irradiance forecasting
3. **Grid Integration**: Net metering and feed-in tariff analysis
4. **Financing Models**: Loan, lease, PPA calculations

## Kenya-Specific Considerations

### Solar Resource Data
- **Latitude Range**: 4°S to 5°N (excellent solar resource)
- **Average GHI**: 4.5-6.5 kWh/m²/day depending on location
- **Seasonal Variation**: ±15% from annual average
- **Rainy Seasons**: March-May, October-December

### Regulatory Framework
- **Kenya Bureau of Standards**: KS 2823 (Solar PV systems)
- **Energy and Petroleum Regulatory Authority (EPRA)**: Grid connection standards
- **Net Metering Regulations**: Current policies and feed-in tariffs

### Local Factors
- **Dust Loading**: 2-5% soiling losses (higher in arid regions)
- **Temperature**: 15-35°C range affects panel efficiency
- **Altitude Effects**: Reduced air density improves irradiance
- **Humidity**: Affects inverter cooling requirements

## Professional Validation
The enhanced calculator should be validated against:
1. **PVsyst** (industry standard modeling software)
2. **NREL PVWatts** (validated against measured data)
3. **Local Installation Data** (actual performance monitoring)

This approach ensures calculations meet international engineering standards while accounting for Kenya's specific solar resource and market conditions.
