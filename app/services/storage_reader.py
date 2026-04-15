import os
import time
import traceback
import subprocess
import ctypes
import psutil

class StorageTemperatureReader:
    """Enhanced temperature reader with priority-based fallback"""
    
    def __init__(self, apply_adjustment=False):
        self.wmi_available = False
        self.ohm_available = False
        self.current_temp_source = "Unknown"
        
        # Adjustment configuration
        self.apply_adjustment = apply_adjustment
        self.storage_adjustment = 13
        self.gpu_adjustment = 8
        self.cpu_adjustment = 10
        
        self.initialize_wmi()
    
    def set_adjustments(self, storage_adj=13, gpu_adj=8, cpu_adj=10, apply_adj=False):
        """Configure temperature adjustments"""
        self.storage_adjustment = storage_adj
        self.gpu_adjustment = gpu_adj
        self.cpu_adjustment = cpu_adj
        self.apply_adjustment = apply_adj
    
    def initialize_wmi(self):
        """Initialize WMI connection"""
        try:
            import wmi
            self.wmi_available = True
            
            # Test OpenHardwareMonitor
            try:
                w = wmi.WMI(namespace="root\\OpenHardwareMonitor")
                sensors = w.Sensor()
                self.ohm_available = True
                print("✅ OpenHardwareMonitor detected")
            except Exception:
                print("❌ OpenHardwareMonitor not detected")
                
        except ImportError:
            print("❌ WMI not available")
    
    def run_openhardware_monitor(self):
        """Run OpenHardwareMonitor.exe"""
        print("\n" + "="*60)
        print("STARTING OPENHARDWAREMONITOR")
        print("="*60)
        
        try:
            # Check if already running
            for proc in psutil.process_iter(['name']):
                try:
                    if proc.info['name'] and 'OpenHardwareMonitor' in proc.info['name']:
                        print("✅ OpenHardwareMonitor is already running")
                        return True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Find OpenHardwareMonitor.exe
            possible_paths = [
                "OpenHardwareMonitor.exe",
                os.path.join(os.getcwd(), "OpenHardwareMonitor.exe"),
                os.path.join(os.path.expanduser("~"), "Desktop", "OpenHardwareMonitor.exe"),
                os.path.join(os.path.expanduser("~"), "Downloads", "OpenHardwareMonitor.exe"),
                r"C:\Program Files\OpenHardwareMonitor\OpenHardwareMonitor.exe",
            ]
            
            found_path = None
            for path in possible_paths:
                if os.path.exists(path):
                    found_path = path
                    break
            
            if not found_path:
                print("⚠️ OpenHardwareMonitor.exe not found")
                return False
            
            # Try to run
            try:
                is_admin = ctypes.windll.shell32.IsUserAnAdmin()
                
                if is_admin:
                    process = subprocess.Popen(
                        [found_path],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        creationflags=subprocess.CREATE_NO_WINDOW
                    )
                    print(f"✅ Process started: {process.pid}")
                else:
                    os.startfile(found_path)
                    print("✅ Started OpenHardwareMonitor")
                
                # Wait for startup
                time.sleep(5)
                
                # Verify running
                for _ in range(10):
                    for proc in psutil.process_iter(['name']):
                        try:
                            if proc.info['name'] and 'OpenHardwareMonitor' in proc.info['name']:
                                print("✅ OpenHardwareMonitor is now running")
                                return True
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            continue
                    time.sleep(1)
                
                print("⚠️ OpenHardwareMonitor may have started")
                return True
                    
            except Exception as e:
                print(f"❌ Failed to launch: {e}")
                return False
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    def _get_all_temperature_sensors(self):
        """Get all temperature sensors from OpenHardwareMonitor"""
        if not self.ohm_available:
            return []
        
        try:
            import wmi
            w = wmi.WMI(namespace="root\\OpenHardwareMonitor")
            sensors = w.Sensor()
            
            temp_sensors = []
            for sensor in sensors:
                if (sensor.SensorType == "Temperature" and 
                    sensor.Value is not None and 
                    sensor.Value != 0):
                    
                    sensor_data = {
                        'name': sensor.Name if hasattr(sensor, 'Name') else "Unknown",
                        'value': float(sensor.Value),
                        'parent': sensor.Parent if hasattr(sensor, 'Parent') else "Unknown",
                        'identifier': sensor.Identifier if hasattr(sensor, 'Identifier') else "Unknown",
                    }
                    temp_sensors.append(sensor_data)
            
            return temp_sensors
            
        except Exception as e:
            print(f"❌ Error reading sensors: {e}")
            return []
    
    def _is_storage_sensor(self, sensor_name, parent_name):
        """Check if sensor belongs to storage"""
        storage_keywords = [
            'hdd', 'ssd', 'disk', 'drive', 'nvme', 'sata', 
            'hard disk', 'solid state', 'samsung', 'crucial',
            'western digital', 'seagate', 'kingston', 'adata',
            'sandisk', 'intel ssd', 'toshiba', 'hitachi',
            'm.2', 'pcie', 'usb', 'external'
        ]
        
        sensor_lower = sensor_name.lower()
        parent_lower = parent_name.lower() if parent_name else ""
        
        if "temperature" in sensor_lower:
            if any(keyword in parent_lower for keyword in storage_keywords):
                return True
            if any(keyword in sensor_lower for keyword in storage_keywords):
                return True
        
        return False
    
    def _is_gpu_sensor(self, sensor_name, parent_name):
        """Check if sensor belongs to GPU"""
        gpu_keywords = [
            'gpu', 'graphics', 'nvidia', 'amd', 'radeon',
            'geforce', 'rtx', 'gtx', 'radeon', 'vega'
        ]
        
        sensor_lower = sensor_name.lower()
        parent_lower = parent_name.lower() if parent_name else ""
        
        if "temperature" in sensor_lower or "temp" in sensor_lower:
            if any(keyword in parent_lower for keyword in gpu_keywords):
                return True
            if any(keyword in sensor_lower for keyword in gpu_keywords):
                return True
        
        return False
    
    def _is_cpu_sensor(self, sensor_name, parent_name):
        """Check if sensor belongs to CPU"""
        cpu_keywords = [
            'cpu', 'processor', 'core', 'package',
            'intel', 'amd', 'ryzen', 'i3', 'i5', 'i7', 'i9'
        ]
        
        sensor_lower = sensor_name.lower()
        parent_lower = parent_name.lower() if parent_name else ""
        
        if "temperature" in sensor_lower or "temp" in sensor_lower:
            if any(keyword in parent_lower for keyword in cpu_keywords):
                return True
            if any(keyword in sensor_lower for keyword in cpu_keywords):
                return True
        
        return False
    
    def get_primary_temperature(self):
        """
        Priority-based temperature detection:
        1. Storage temperatures
        2. GPU temperatures
        3. CPU temperatures
        4. Any temperature sensor
        """
        temp_sensors = self._get_all_temperature_sensors()
        
        if not temp_sensors:
            self.current_temp_source = "No sensors found"
            return None
        
        # Priority 1: Storage temperatures
        storage_temps = []
        for sensor in temp_sensors:
            if self._is_storage_sensor(sensor['name'], sensor['parent']):
                storage_temps.append(sensor)
        
        if storage_temps:
            avg_temp = sum(s['value'] for s in storage_temps) / len(storage_temps)
            
            # Apply adjustment only if configured
            if self.apply_adjustment:
                adjusted_temp = avg_temp - self.storage_adjustment
                self.current_temp_source = f"Storage ({len(storage_temps)} devices)"
                print(f"📊 Using storage temperatures: {adjusted_temp:.1f}°C (adjusted by -{self.storage_adjustment}°C)")
                return adjusted_temp
            else:
                self.current_temp_source = f"Storage ({len(storage_temps)} devices)"
                return avg_temp
        
        # Priority 2: GPU temperatures
        gpu_temps = []
        for sensor in temp_sensors:
            if self._is_gpu_sensor(sensor['name'], sensor['parent']):
                gpu_temps.append(sensor)
        
        if gpu_temps:
            avg_temp = sum(s['value'] for s in gpu_temps) / len(gpu_temps)
            
            # Apply adjustment only if configured
            if self.apply_adjustment:
                adjusted_temp = avg_temp - self.gpu_adjustment
                self.current_temp_source = f"GPU ({len(gpu_temps)} sensors)"
                print(f"🎮 Using GPU temperatures: {adjusted_temp:.1f}°C (adjusted by -{self.gpu_adjustment}°C)")
                return adjusted_temp
            else:
                self.current_temp_source = f"GPU ({len(gpu_temps)} sensors)"
                print(f"🎮 Using GPU temperatures: {avg_temp:.1f}°C (raw)")
                return avg_temp
        
        # Priority 3: CPU temperatures
        cpu_temps = []
        for sensor in temp_sensors:
            if self._is_cpu_sensor(sensor['name'], sensor['parent']):
                cpu_temps.append(sensor)
        
        if cpu_temps:
            # Try CPU package first
            package_temp = None
            for sensor in cpu_temps:
                if 'package' in sensor['name'].lower():
                    package_temp = sensor['value']
                    if self.apply_adjustment:
                        adjusted_temp = package_temp - self.cpu_adjustment
                        self.current_temp_source = "CPU Package"
                        print(f"⚡ Using CPU package: {adjusted_temp:.1f}°C (adjusted by -{self.cpu_adjustment}°C)")
                        return adjusted_temp
                    else:
                        self.current_temp_source = "CPU Package"
                        print(f"⚡ Using CPU package: {package_temp:.1f}°C (raw)")
                        return package_temp
            
            # Otherwise average of CPU cores
            avg_temp = sum(s['value'] for s in cpu_temps) / len(cpu_temps)
            
            if self.apply_adjustment:
                adjusted_temp = avg_temp - self.cpu_adjustment
                self.current_temp_source = f"CPU ({len(cpu_temps)} cores)"
                print(f"⚡ Using CPU temperatures: {adjusted_temp:.1f}°C (adjusted by -{self.cpu_adjustment}°C)")
                return adjusted_temp
            else:
                self.current_temp_source = f"CPU ({len(cpu_temps)} cores)"
                print(f"⚡ Using CPU temperatures: {avg_temp:.1f}°C (raw)")
                return avg_temp
        
        # Priority 4: Any temperature sensor
        if temp_sensors:
            temp = temp_sensors[0]['value']
            source_name = temp_sensors[0]['name']
            self.current_temp_source = f"Generic ({source_name})"
            print(f"📈 Using generic sensor: {temp:.1f}°C")
            return temp
        
        self.current_temp_source = "No suitable sensors"
        return None
    
    def get_all_sensor_info(self):
        """Get detailed sensor information"""
        temp_sensors = self._get_all_temperature_sensors()
        
        if not temp_sensors:
            return "No temperature sensors found"
        
        info_lines = ["=== AVAILABLE TEMPERATURE SENSORS ==="]
        
        # Categorize sensors
        storage_sensors = []
        gpu_sensors = []
        cpu_sensors = []
        other_sensors = []
        
        for sensor in temp_sensors:
            if self._is_storage_sensor(sensor['name'], sensor['parent']):
                storage_sensors.append(sensor)
            elif self._is_gpu_sensor(sensor['name'], sensor['parent']):
                gpu_sensors.append(sensor)
            elif self._is_cpu_sensor(sensor['name'], sensor['parent']):
                cpu_sensors.append(sensor)
            else:
                other_sensors.append(sensor)
        
        info_lines.append(f"\n📊 STORAGE Sensors ({len(storage_sensors)}):")
        for sensor in storage_sensors:
            info_lines.append(f"  • {sensor['name']}: {sensor['value']:.1f}°C (Parent: {sensor['parent']})")
        
        info_lines.append(f"\n🎮 GPU Sensors ({len(gpu_sensors)}):")
        for sensor in gpu_sensors:
            info_lines.append(f"  • {sensor['name']}: {sensor['value']:.1f}°C (Parent: {sensor['parent']})")
        
        info_lines.append(f"\n⚡ CPU Sensors ({len(cpu_sensors)}):")
        for sensor in cpu_sensors:
            info_lines.append(f"  • {sensor['name']}: {sensor['value']:.1f}°C (Parent: {sensor['parent']})")
        
        info_lines.append(f"\n❓ Other Sensors ({len(other_sensors)}):")
        for sensor in other_sensors:
            info_lines.append(f"  • {sensor['name']}: {sensor['value']:.1f}°C (Parent: {sensor['parent']})")
        
        info_lines.append(f"\n📈 Currently using: {self.current_temp_source}")
        
        # Add adjustment info
        info_lines.append(f"\n🔧 ADJUSTMENT SETTINGS:")
        info_lines.append(f"  • Apply adjustment: {self.apply_adjustment}")
        info_lines.append(f"  • Storage adjustment: -{self.storage_adjustment}°C")
        info_lines.append(f"  • GPU adjustment: -{self.gpu_adjustment}°C")
        info_lines.append(f"  • CPU adjustment: -{self.cpu_adjustment}°C")
        
        return "\n".join(info_lines)
    
    def get_temperature_source(self):
        return self.current_temp_source
    
    def get_current_sensor_type(self):
        """Get the type of sensor currently being used"""
        temp_sensors = self._get_all_temperature_sensors()
        
        if not temp_sensors:
            return "No sensors"
        
        # Check storage first
        for sensor in temp_sensors:
            if self._is_storage_sensor(sensor['name'], sensor['parent']):
                return "Storage"
        
        # Check GPU
        for sensor in temp_sensors:
            if self._is_gpu_sensor(sensor['name'], sensor['parent']):
                return "GPU"
        
        # Check CPU
        for sensor in temp_sensors:
            if self._is_cpu_sensor(sensor['name'], sensor['parent']):
                return "CPU"
        
        return "Generic"