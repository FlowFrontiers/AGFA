# Adaptive Gradual Flow Aggregation Demo Tool
The critical role of network traffic measurement and analysis extends across a range of network operations, ensuring quality of service, security, and efficient resource management. Despite the ubiquity of flow-level measurement, the escalating size of flow entries presents significant scalability issues. This study explores the implications of adaptive gradual flow aggregation, a solution devised to mitigate these challenges, on flow information distortion. The investigation maintains flow records in buffers of varying aggregation levels, iteratively adjusted based on the changing traffic load mirrored in CPU and memory utilization. Findings underscore the efficiency of adaptive gradual flow aggregation, particularly when applied to a specific buffer, yielding an optimal balance between information preservation and memory utilization. The paper highlights the particular significance of this approach in Internet of Things (IoT) and contrasted environments, characterized by stringent resource constraints. Consequently, it casts light on the imperative for adaptability in flow aggregation methods, the impact of these techniques on information distortion, and their influence on network operations. This research offers a foundation for future studies targeting the development of more adaptive and effective flow measurement techniques in diverse and resource-limited network environments.

## Table of Contents
* [Main Features](#main-features)
* [Usage](#usage)
    * [Prerequisite](#prerequisite)
    * [Run](#run)
* [Credits](#credits)
  * [Authors](#authors)
* [Acknowledgement](#acknowledgement)
* [License](#license)

## Main Features
- Efficient flow measurement and analysis
- Adaptive gradual flow aggregation to mitigate scalability issues
- Maintains flow records in buffers of varying aggregation levels
- Buffers are iteratively adjusted based on changing traffic load
- Optimal balance between information preservation and memory utilization
- Command line interface with various arguments for customization
- Dynamic thresholding, payload comparison, and advanced IP comparison
- Graphical visualization of data

## Usage
After a successful installation of requirements, be sure to adjust the configuration files to ensure that the solution works for your needs.

To install the required packages, run the following command:

```
pip3 install -r requirements.txt
```

### Prerequisite
- Operating system (with hardware) that supports NFStream==6.0.0
- Python 3.9

### Run
To start the Network Buffering Tool v2.0, you can use the command line interface with the following arguments:

- **-i** or **--initialize**: Use default.ini file for config. {True/False}
- **-sc** or **--source**: Set the capture source ethernet interface/pcap file. {String}
- **-t** or **--threshold**: Set default Threshold value. {Float}
- **-s** or **--sliding**: Set default value for sliding window. {Integer}
- **-b** or **-buffer**: Set buffer parameter concentration list of fields. {String array}
- **-mi** or **--min**: Merge columns by minimum value of fields. {String array}
- **-ma** or **--max**: Merge columns by maximum value of fields. {String array}
- **-a** or **-accumulate**: Accumulate columns by fields. {String array}
- **-c** or **--concat**: Concat columns. {String array}
- **-d** or **-drop**: Drop fields. {String array}
- **-dt** or **--dynamicThreshold**: Enable dynamic thresholding. {True/False}
- **-pc** or **--payloadComparison**: Switch payload comparison. {True/False}
- **-aipc** or **--advancedIPComparison**: Switch to advanced IP comparison. {True/False}
- **-mc** or **--memoryC**: Switch memory comparison mode. True for all process memory total. False for just the python script usage of total. {True/False}
- **-act** or **--ARUCriticalThreshold**: Set ARU critical value for thresholding. {Float}
- **-e** or **--exporterStep**: Set exporter step time for generate data. Set-up to 0 if you want to turn it off. {Integer}
- **-al** or **--graphLength**: Set graphs x-axis length for visualize data. {Integer}
- **-f** or **--aggregationFrequency**: Set aggregation frequency (ms). {Float}
- **-w** or **--width**: Set exporter graphs width (pixel). {Integer}
- **-hi** or **--height**: Set exporter graphs height (pixel). {Integer}
- **-rms** or **--relativememorysize**: Set the relative memory size (packet count). {Integer}
To start the tool using the command line parameters, run the following command:

```
python3 main.py \
  -t 100000 \
  -s 10 \
  -b protocol src_port dst_port src_ip dst_ip \
  -mi bidirectional_first_seen_ms src2dst_first_seen_ms dst2src_first_seen_ms \
  -ma bidirectional_last_seen_ms src2dst_last_seen_ms dst2src_last_seen_ms \
  -a bidirectional_packets bidirectional_raw_bytes bidirectional_ip_bytes bidirectional_duration_ms src2dst_packets src2dst_raw_bytes src2dst_ip_bytes src2dst_duration_ms dst2src_packets dst2src_raw_bytes dst2src_ip_bytes dst2src_duration_ms \
  -d id version vlan_id src_ip_type dst_ip_type expiration_id \
  -dt False \
  -pc False \
  -aipc False \
  -act 98
```

If you want to use the default config file, set the **-i** or **--initialize** argument to True. If you do not have the default config file, you will need to use the console configuration.

## Credits
### Authors
* Adrian Pekar
* Laszlo A. Makara
* Winston K. G. Seah
* Oscar Mauricio Caicdeo Rendon

## Acknowledgement
This work was supported by the János Bolyai Research Scholarship of the Hungarian Academy of Sciences. 
Supported by the ÚNKP-23-5-BME-461 New National Excellence Program of the Ministry for Culture and Innovation from the source of the National Research, Development and Innovation Fund. 
The work presented in this paper was supported by project no. TKP2021-NVA-02. Project no. TKP2021-NVA-02 has been implemented with the support provided by the Ministry of Culture and Innovation of Hungary from the National Research, Development and Innovation Fund, financed under the TKP2021-NVA funding scheme.
## License
This project is licensed under the LGPLv3 license - see the [License](LICENSE) file for details.
