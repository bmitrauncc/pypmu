from synchrophasor.pdc import Pdc
from synchrophasor.frame import DataFrame
import socket


def run_pdc(n_msg=10, ip=None, port=50000, pdc_id=1):

    if ip is None:
        ip = socket.gethostbyname(socket.gethostname())
    
    pdc = Pdc(pdc_id=pdc_id, pmu_ip=ip, pmu_port=port)
    pdc.logger.setLevel("DEBUG")

    pdc.run()  # Connect to PMU
    
    # pdc.stop()
    config = pdc.get_config()  # Get configuration from PMU
    # header = pdc.get_header()

    pdc.start()  # Request to start sending measurements
   
    i = 0
    data_array = []
    while i < n_msg:
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
