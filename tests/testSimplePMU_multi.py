import time
from synchrophasor.simplePMU import SimplePMU
from synchrophasor.pdc import Pdc
import socket
from synchrophasor.frame import DataFrame
import socket
import multiprocessing as mp


def run_pmu(n_msg):
    publish_frequency = 5

    ip = socket.gethostbyname(socket.gethostname())
    port = 50000

    station_names = ['PMU1', 'PMU2', 'PMU3']
    channel_names = [
        ['Phasor1.1', 'Phasor1.2'],
        ['Phasor2.1', 'Phasor2.2', 'Phasor2.3'],
        ['Phasor3.1'],
    ]
    channel_types = [
        ['v', 'i'],
        ['v', 'i', 'v'],
        ['i'],
    ]
    id_codes = [1410, 1411, 1412]
    pdc_id = 1

    # station_names = ['PMU1']
    # channel_names = [['Phasor1.1', 'Phasor1.2']]
    pmu = SimplePMU(
        ip, port,
        publish_frequency=publish_frequency,
        station_names=station_names,
        channel_names=channel_names,
        pdc_id=pdc_id,
        channel_types=channel_types,
        id_codes=id_codes
    )
    pmu.run()

    k = 0
    while k < n_msg:
        # time.sleep(1/publish_frequency)
        if pmu.pmu.clients:  # Check if there is any connected PDCs
            k += 1
            # print(k)
            # t, v = input_signal

            # Publish C37.118-snapshot
            # pmu_data = [(mag, ang) for mag, ang in zip(np.abs(v), np.angle(v))]
            pmu.publish()

    time.sleep(1)
    # pmu.cleanup()
    # # sys.exit()
    # import threading
    # for thread in threading.enumerate():
    #     print(thread.name)

def run_pdc(n_msg):

    ip = socket.gethostbyname(socket.gethostname())
    pdc = Pdc(pdc_id=1, pmu_ip=ip, pmu_port=50000)
    pdc.logger.setLevel("DEBUG")

    pdc.run()  # Connect to PMU
    
    # pdc.stop()
    config = pdc.get_config()  # Get configuration from PMU
    header = pdc.get_header()

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



if __name__ == '__main__':
    n_msg = 10
    pmu_process = mp.Process(target=run_pmu, args=(n_msg,))
    pdc_process = mp.Process(target=run_pdc, args=(n_msg,))

    pmu_process.start()
    pdc_process.start()

    print('Finished')
