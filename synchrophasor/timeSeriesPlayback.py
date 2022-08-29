import numpy as np
from synchrophasor.simplePMU import SimplePMU
import threading
import time

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

