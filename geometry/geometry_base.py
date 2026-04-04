import json
import numpy as np

class HullGeometryBase:
    """
    Base class for handling hull geometry constraints and initial hydrostatic 
    calculations based on component distribution and hull specifications.
    """
    def __init__(self, config_path):
        """
        Initialize the geometry handler by loading the JSON configuration.
        """
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        self.constraints = self.config['hull_constraints']
        self.components = self.config['component_boxes']
        
        # Physical constants: Density of Salt Water (approx. 1025 kg/m^3)
        # Converted to kg/mm^3 to match JSON millimeter-based units.
        self.RHO_SW = 1025 / 1e9 

    def calculate_displacement(self):
        """
        Calculate required volumetric displacement per hull based on 
        Archimedes' principle and user-defined mass distribution.
        """
        # Note: Fixed the key name from 'distrubuted_mass' to 'mass' logic if applicable,
        # and corrected 'ddisplacement_range' typo.
        total_mass = sum(comp['mass'] for comp in self.components)

        # Calculate the target buoyancy distribution fraction for the center hull
        # based on the defined range in the constraints.
        target_fraction = sum(self.constraints['displacement_range']) / 2

        mass_center = total_mass * target_fraction
        
        # Calculate displacement for side hulls (Amasi)
        # Remaining mass is divided equally among the secondary hulls.
        n_side_hulls = self.constraints['number_of_hulls'] - 1
        mass_per_side = (total_mass * (1 - target_fraction)) / n_side_hulls

        return {
            "center_vol_mm3": mass_center / self.RHO_SW,
            "side_vol_mm3": mass_per_side / self.RHO_SW,
            "total_mass_kg": total_mass
        }
    
    def check_component_fit(self):
        """
        Validate that internal components physically fit within the 
        global hull envelope constraints (Length and Beam).
        """
        max_L = self.constraints['max_length']
        max_B = self.constraints['max_beam']
        
        for comp in self.components:
            l, b, h = comp['dimensions']
            if l > max_L or b > max_B:
                # Using academic terminology for error reporting
                print(f"CRITICAL CONSTRAINT VIOLATION: Component '{comp['name']}' "
                      f"exceeds maximum hull dimensions.")
                return False
        return True
    
    def get_side_hull_bounds(self):
        """
        Determine the spatial boundaries and 'Keep-out' zones for the 
        side hulls to prevent interference with propulsors or structural limits.
        """
        max_L_side = self.constraints['max_side_hull_length']
        
        return {
            "max_length": max_L_side,
            "y_offset_min": self.constraints['min_hull_spacing']
        }

# --- Main Entry Point for Local Validation ---    
if __name__ == "__main__":
    geo = HullGeometryBase('project_config.json')
    
    # Corrected method call to match the defined calculate_displacement
    vols = geo.calculate_displacement()
    
    if geo.check_component_fit():
        print(f"Project: {geo.config['project_name']}")
        print(f"Required Center Hull Buoyancy: {vols['center_vol_mm3']/1e6:.2f} Liters")
        print(f"Side Hull Length Constraint: {geo.get_side_hull_bounds()['max_length']} mm")