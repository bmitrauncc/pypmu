import numpy as np
from synchrophasor.simplePMU import SimplePMU
import threading
import time
import matplotlib.pyplot as plt

"""
tinyPMU will listen on ip:port for incoming connections.
When tinyPMU receives command to start sending
measurements - fixed (sample) measurement will
be sent.
"""


class PMUTimeSeriesPublisher(SimplePMU):
    def __init__(self, *args, time, phasors, station_names=None, channel_names=None, publish_frequency=None, **kwargs):

        n_pmus = len(phasors)
        n_phasors_per_pmu = [len(phasors_) for phasors_ in phasors]
        if channel_names is None:
            channel_names = [["Ph{}".format(i) for i in range(n_phasors_pmu)] for n_phasors_pmu in len(n_phasors_per_pmu)]

        if station_names is None:
            station_names = ["PMU{}".format(i) for i in range(n_pmus)]

        self.time = time
        self.phasors = phasors
        self.speed = 1

        self._stopped = False
        # pmu.run()
        self.dt = round(1e3*np.mean(self.time[1:] - self.time[:-1]))*1e-3

        if publish_frequency is None:
            self.publish_frequency = round(1/self.dt)

        super().__init__(
            *args,
            channel_names=channel_names,
            station_names=station_names,
            set_timestamp=False,
            publish_frequency=self.publish_frequency,
            **kwargs
        )

        self.pause_cv = threading.Condition()
        self.paused = False

    def toggle_pause(self):
        self.paused = not self.paused
        with self.pause_cv:
            self.pause_cv.notify()

    def stop(self):
        self._stopped = True

    def main_loop(self):
        self.k_sim = 0
        # t_world = 0
        t_world = self.time[0]
        t_prev = time.time()
        self.time_stamp = self.time[0]

        while not self._stopped:

            with self.pause_cv:
                while self.paused:
                    self.pause_cv.wait()
                    t_prev = time.time()

            # self.time_stamp = self.time[self.k_sim]
            self.time_stamp += self.dt  # self.time[self.k_sim]
            pmu_data = []
            for phasor_data in self.phasors:
                phasors_complex = phasor_data[self.k_sim, :]
                pmu_data.append([(abs(ph), np.angle(ph)) for ph in phasors_complex])

            if len(self.phasors) == 1:
                pmu_data = pmu_data[0]

            if self.pmu.clients:  # Check if there is any connected PDCs
                # print('Main loop running')
                self.publish(self.time_stamp, pmu_data)
                # self.publish()

            self.k_sim += 1
            if self.k_sim >= len(self.time):
                self.k_sim -= len(self.time)

            # Code for synchronizing with wall clock time
            dt_loop = time.time() - t_prev  # Actual time spent on current loop
            t_prev = time.time()

            t_world += dt_loop * self.speed
            dt_err = self.time_stamp - t_world
            if dt_err > 0:
                # print(t_world, self.time_stamp)
                time.sleep(dt_err / self.speed)
            elif dt_err <= 0:
                pass

            dt_ideal = self.dt / self.speed

        print('PMU publisher loop finished.')
        # self.cleanup()


if __name__ == "__main__":
    # __file__ = r'/synchrophasor/timeSeriesPlayback.py'
    t_end = 10
    dt = 0.02

    # List of PMUs
    station_names = ['PMU1', 'PMU2', 'PMU3']

    # List of list of channels pr. PMU
    channel_names = [
        ['Phasor1.1', 'Phasor1.2'],
        ['Phasor2.1', 'Phasor2.2', 'Phasor2.3'],
        ['Phasor3.1'],
    ]

    # Generate some random time series
    t = np.arange(0, t_end, dt)
    phasor_data = []
    for channel_names_ in channel_names:
        angles = 1e-2*np.cumsum(np.random.randn(len(t), len(channel_names_)), axis=0)
        magnitudes = 1 + 1e-3*np.cumsum(np.random.randn(len(t), len(channel_names_)), axis=0)
        phasors_pmu = magnitudes*np.exp(1j*angles)
        phasors_pmu -= (phasors_pmu[-1, :] - phasors_pmu[0, :])[None, :] * t[:, None] / (t[-1] - t[0])

        phasor_data.append(phasors_pmu)

    # Plot the time series that are streamed
    fig, ax = plt.subplots(2, len(station_names), squeeze=False, sharex=True, sharey='row')
    for i, (ax_, phasors_pmu) in enumerate(zip(ax.T, phasor_data)):
        ax[0, i].set_title(station_names[i])
        ax[0, i].plot(t, abs(phasors_pmu))
        ax[1, i].plot(t, np.angle(phasors_pmu))
        ax[1, i].set_xlabel('Time [s]')
        ax[1, i].legend(channel_names[i])

    ax[0, 0].set_ylabel('Phasor magnitudes []')
    ax[1, 0].set_ylabel('Phasor angles [rad]')

    # PMU Snapshot Publisher
    # ip = "10.0.0.39"
    import socket
    ip = socket.gethostbyname(socket.gethostname())  # Get local ip automatically
    port = 50000

    pmu_publisher = PMUTimeSeriesPublisher(
        ip, port,
        time=t,
        # publish_frequency=10,  # is determined automatically if not specified
        phasors=phasor_data,
        station_names=station_names,
        channel_names=channel_names
    )
    pmu_publisher.pmu.run()  # Start listening to incoming connections and send data (if published)

    # Run the PMU Publisher in a separate thread to be able to exit
    pmu_thread = threading.Thread(target=pmu_publisher.main_loop, name='PMU-Publisher-Thread')
    pmu_thread.daemon = True
    pmu_thread.start()

    # Continues until the plot window is closed
    plt.show(block=True)
    pmu_publisher.stop()

    # This does not always work as intended, some threads/processes are not always stopped.
    pmu_publisher.cleanup()

    import threading

    for i, thread in enumerate(threading.enumerate()):
        print(thread)

    # for client in pmu_publisher.pmu.clients:
    #     print('Terminating {}'.format(client))
    #     client.terminate()
    #     print('Terminated {}'.format(client))
    #
    # for i, thread in enumerate(threading.enumerate()):
    #     if i > 0:
    #         print('Joining {}'.format(thread))
    #         thread.join()
    #         print('Joined{}'.format(thread))
    #
