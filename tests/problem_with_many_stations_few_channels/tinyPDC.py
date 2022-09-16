from synchrophasor.pdc import Pdc
from synchrophasor.frame import DataFrame

"""
tinyPDC will connect to pmu_ip:pmu_port and send request
for header message, configuration and eventually
to start sending measurements.
"""


if __name__ == "__main__":

    __file__ = r'C:\Users\hallvarh\OneDrive - SINTEF\Projects\NEWEPS\Code\pypmu\examples\tinyPDC.py'

    # ip = "192.168.137.2"
    # port = 4712
    # id = 1010
    import socket
    ip = socket.gethostbyname(socket.gethostname())  # Get local ip automatically
    port = 50001

    id = 1410
    pdc = Pdc(pdc_id=id, pmu_ip=ip, pmu_port=port)
    # pdc.logger.setLevel("DEBUG")

    pdc.run()  # Connect to PMU
    print(pdc.buffer_size)

    header = pdc.get_header()  # Get header message from PMU
    config = pdc.get_config()  # Get configuration from PMU

    pdc.start()  # Request to start sending measurements
    # data = pdc.get()  # Keep receiving data

    while True:

        # while len(received_data) < 4:
        #     received_data += self.pmu_socket.recv(self.buffer_size)
        #
        # bytes_received = len(received_data)
        # total_frame_size = int.from_bytes(received_data[2:4], byteorder="big", signed=False)
        # print(total_frame_size)

        data = pdc.get()  # Keep receiving data

        if type(data) == DataFrame:
            print(data.get_measurements())

        elif data is None:
            print('Not data')
                # pdc.quit()  # Close connection
                # break
        elif isinstance(data, list):
            print('Got multiple data frames')
            for data_ in data:
                print(data_.get_measurements())

            # print('Multiple messages received')
