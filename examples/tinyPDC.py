from synchrophasor.pdc import Pdc
from synchrophasor.frame import DataFrame

"""
tinyPDC will connect to pmu_ip:pmu_port and send request
for header message, configuration and eventually
to start sending measurements.
"""
import socket


if __name__ == "__main__":

    ip = socket.gethostbyname(socket.gethostname())
    pdc = Pdc(pdc_id=1410, pmu_ip=ip, pmu_port=50000)
    pdc.logger.setLevel("DEBUG")

    pdc.run()  # Connect to PMU
    
    # pdc.stop()
    config = pdc.get_config()  # Get configuration from PMU
    header = pdc.get_header()

    pdc.start()  # Request to start sending measurements
   
    i = 0
    data_array = []
    while i < 30:
        data = pdc.get()  # Keep receiving data

        if type(data) == DataFrame:
            data_array.append(data.get_measurements())
        else:
            if not data:
                pdc.quit()  # Close connection
                break

            if len(data)>0:
                for meas in data: 
                    data_array.append(meas.get_measurements())

        i += 1
