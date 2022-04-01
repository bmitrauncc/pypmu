from synchrophasor.frame import ConfigFrame2
from synchrophasor.pmu_mod import PmuMod
import random
import time
import numpy as np
import socket
import queue


class SimplePMU:
    def __init__(self, ip, port, station_names, channel_names, publish_frequency=50, set_timestamp=True):

        self.station_names = station_names
        self.channel_names = channel_names

        self.n_pmus = len(self.station_names)
        # self.n_pmu_channels = [len(channel_names_) for channel_names_ in channel_names]

        # Initialize PMUs
        self.ip = ip
        self.port = port
        self.pmu = PmuMod(ip=self.ip, port=self.port, set_timestamp=set_timestamp, data_rate=publish_frequency)
        self.pmu.logger.setLevel("DEBUG")

        conf_kwargs = dict(
            pmu_id_code=1410,  # PMU_ID
            time_base=1000000,  # TIME_BASE
            num_pmu=self.n_pmus,  # Number of PMUs included in recorded_pmu_data_raw frame
            # station_name='PMU',  # Station name
            id_code=1410,  # Data-stream ID(s)
            data_format=(True, True, True, True),  # Data format - POLAR; PH - REAL; AN - REAL; FREQ - REAL;
            # phasor_num=self.n_phasors,  # Number of phasors
            analog_num=1,  # Number of analog values
            digital_num=1,  # Number of digital status words
            # channel_names=channel_names[0] + [
            #     "ANALOG1", "BREAKER 1 STATUS",
            #     "BREAKER 2 STATUS", "BREAKER 3 STATUS", "BREAKER 4 STATUS", "BREAKER 5 STATUS",
            #     "BREAKER 6 STATUS", "BREAKER 7 STATUS", "BREAKER 8 STATUS", "BREAKER 9 STATUS",
            #     "BREAKER A STATUS", "BREAKER B STATUS", "BREAKER C STATUS", "BREAKER D STATUS",
            #     "BREAKER E STATUS", "BREAKER F STATUS", "BREAKER G STATUS"
            # ],  # Channel Names
            # Conversion factor for phasor channels - (float representation, not important)
            an_units=[(1, "pow")],  # Conversion factor for analog channels
            dig_units=[(0x0000, 0xffff)],  # Mask words for digital status words
            f_nom=50,  # Nominal frequency
            cfg_count=1,  # Configuration change count
            data_rate=publish_frequency
        )

        other_channel_names = [
            "ANALOG1", "BREAKER 1 STATUS",
            "BREAKER 2 STATUS", "BREAKER 3 STATUS", "BREAKER 4 STATUS", "BREAKER 5 STATUS",
            "BREAKER 6 STATUS", "BREAKER 7 STATUS", "BREAKER 8 STATUS", "BREAKER 9 STATUS",
            "BREAKER A STATUS", "BREAKER B STATUS", "BREAKER C STATUS", "BREAKER D STATUS",
            "BREAKER E STATUS", "BREAKER F STATUS", "BREAKER G STATUS"
        ]
        if self.n_pmus == 1:
            self.n_phasors = len(self.channel_names[0])
            conf_kwargs['station_name'] = station_names[0]  # 'PMU'
            conf_kwargs['ph_units'] = [(0, "v")]*self.n_phasors
            conf_kwargs['channel_names'] = self.channel_names[0] + other_channel_names
            conf_kwargs['phasor_num'] = self.n_phasors
        else:
            self.n_phasors_per_pmu = [len(channel_names_) for channel_names_ in self.channel_names]
            conf_kwargs['phasor_num'] = self.n_phasors_per_pmu
            conf_kwargs['ph_units'] = [[(0, "v")]*n_phasors_per_pmu for n_phasors_per_pmu in self.n_phasors_per_pmu]
            conf_kwargs['id_code'] = list(range(conf_kwargs['id_code'], conf_kwargs['id_code'] + self.n_pmus))
            conf_kwargs['station_name'] = self.station_names
            conf_kwargs['channel_names'] = [channel_names_ + other_channel_names for channel_names_ in self.channel_names]
            for key in ['data_format', 'analog_num', 'digital_num', 'an_units', 'dig_units', 'f_nom', 'cfg_count']:
                conf_kwargs[key] = [conf_kwargs[key]] * self.n_pmus

        cfg = ConfigFrame2(**conf_kwargs)

        self.pmu.set_configuration(cfg)
        self.pmu.set_header("My PMU-Stream")

        self.run = self.pmu.run

    def cleanup(self):
        # This does not always work...
        self.pmu.stop()
        # print('SimplePMU stopped.')
        # print('Connecting to listener socket')
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((self.ip, self.port))
        # print('Closing listener socket')
        self.pmu.socket.close()
        # print('Joining listener')
        self.pmu.listener.join()
        # print('Stopping PDC handler processes')
        for stop_event in self.pmu.client_stop_events:
            stop_event.set()

        # print('Emptying client buffers')
        # Empty queues (remaining items might cause main process to not exit)
        for i, client_buffer in enumerate(self.pmu.client_buffers):
            k = 0
            try:
                while True:
                    client_buffer.get(False)
                    k += 1
            except queue.Empty:
                # print('Client buffer {} emptied.'.format(i))
                pass

        print('Done.')

    def publish(self, time_stamp=None, phasor_data=None):

        if time_stamp is None:
            time_stamp = time.time()

        # soc = int(time_stamp)
        # frasec = int((((repr((time_stamp % 1))).split("."))[1])[0:6])
        # frasec = int(format(time_stamp % 1, '.6f').split(".")[1])
        soc, frasec = [int(val) for val in format(time_stamp, '.6f').split(".")]

        data_kwargs = dict(
            soc=soc,
            frasec=(frasec, '+'),
            analog=[9.91],
            digital=[0x0001],
            stat=("ok", True, "timestamp", False, False, False, 0, "<10", 0),
            freq=0,  #10 + np.random.randn(1)*1e-1,
            dfreq=0,
        )

        if phasor_data is None:
            if self.n_pmus == 1:
                data_kwargs['phasors'] = [(random.uniform(215.0, 240.0), random.uniform(-np.pi, np.pi)) for _ in range(self.n_phasors)]
            else:
                data_kwargs['phasors'] = [[(random.uniform(215.0, 240.0), random.uniform(-np.pi, np.pi)) for _ in
                               range(n_phasors_per_pmu)] for n_phasors_per_pmu in self.n_phasors_per_pmu]

        # if self.n_pmus > 1:
        #     data_kwargs['phasors'] = [phasor_data] * self.n_pmus
        else:
            data_kwargs['phasors'] = phasor_data

        if self.n_pmus > 1:
            for key in ['analog', 'digital', 'stat', 'freq', 'dfreq']:
                data_kwargs[key] = [data_kwargs[key]]*self.n_pmus

        self.pmu.send_data(**data_kwargs)


if __name__ == '__main__':

    publish_frequency = 5
    ip = '10.0.0.39'
    port = 50000

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
        time.sleep(0.1)
        if pmu.pmu.clients:  # Check if there is any connected PDCs
            k += 1
            print(k)
            # t, v = input_signal

            # Publish C37.118-snapshot
            # pmu_data = [(mag, ang) for mag, ang in zip(np.abs(v), np.angle(v))]
            pmu.publish()

    pmu.cleanup()
    # sys.exit()
    import threading
    for thread in threading.enumerate():
        print(thread.name)