import time
from synchrophasor.simplePMU import SimplePMU
import socket


if __name__ == '__main__':

    publish_frequency = 5

    ip = socket.gethostbyname(socket.gethostname())
    port = 50001

    station_names = ['PMU1', 'PMU2', 'PMU3']
    channel_names = [
        ['Phasor1.1', 'Phasor1.2'],
        ['Phasor2.1', 'Phasor2.2', 'Phasor2.3'],
        ['Phasor3.1'],
    ]

    # station_names = ['PMU1']
    # channel_names = [['Phasor1.1', 'Phasor1.2']]
    pmu = SimplePMU(
        ip, port,
        publish_frequency=publish_frequency,
        station_names=station_names,
        channel_names=channel_names,
    )
    pmu.run()

    k = 0
    while k < 200:
        time.sleep(1/publish_frequency)
        if pmu.pmu.clients:  # Check if there is any connected PDCs
            k += 1
            print(k)
            # t, v = input_signal

            # Publish C37.118-snapshot
            # pmu_data = [(mag, ang) for mag, ang in zip(np.abs(v), np.angle(v))]
            pmu.publish()

    pmu.cleanup()
    # # sys.exit()
    # import threading
    # for thread in threading.enumerate():
    #     print(thread.name)