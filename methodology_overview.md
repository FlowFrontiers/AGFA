# Adaptive Multi-Buffer Flow Measurement Strategy

## Objective
Maximize the granularity and accuracy of flow statistics within resource constraints, while ensuring an adaptive response to changes in resource usage, ensuring efficient system operation. 

As resources are abundant, more detailed flow data is retained, and conversely, as resources diminish, the detail level of flow data is adaptively reduced to fit within the resource constraints.


## Gradual Flow Key Reduction

The cornerstone of this strategy resides in the _Gradual Flow Key Reduction_ [[1]](#Irino2008) mechanism, which orchestrates a controlled, progressive aggregation of flow data by judiciously reducing the flow key elements as data navigates through a sequence of buffers.

- **Flow Key Precedence**: Central to this process is the establishment of a _Flow Key Precedence_, delineating the order of reduction of flow key elements: from the most significant to the least significant. Each reduction phase engenders a new set of flow records exhibiting varying levels of granularity, transitioning from the most detailed to the coarsest.

- **Adaptive Buffer Structure**: Rooted in the assumption of utilizing a common 5-tuple, the methodology unfolds over five buffers from `B0` to `B4`. However, the architecture embodies adaptability, allowing for a tailored buffer structure should a different number of flow key elements define the flows. The number of buffers can be modulated to resonate with the number of flow key elements, ensuring a harmonious alignment with varying flow definitions.

- **Structured Flow Movement and Aggregation**: As flows advance to a buffer with diminished granularity, certain flow details are relinquished, and statistics of flows that resonate in the remaining flow details are amalgamated. This regimented reduction and transit across buffers engender a balanced trade-off between information retention and resource utilization.

- **Enhanced Aggregation Pathway**: Diverging from the original method where **flows leap directly from the main buffer to a designated buffer predicated on the current reduction round**, our methodology facilitates a more structured, and stepwise aggregation process. This gradual movement potentially fosters a more judicious information preservation, enhancing the trade-off between data granularity and resource constraints.

## Buffers

The methodology is grounded on a hierarchical buffer system, where each buffer signifies a particular level of flow key aggregation, hence orchestrating a structured data reduction trajectory.

For the elucidation of the buffer hierarchy, an assumption is made employing a common 5-tuple flow key set with a specific precedence order: `protocol` > `src_port` > `dst_port` > `src_ip` > `dst_ip`.

- **Buffer B0 (Main Flow Cache)**: At this level, the full spectrum of flow details is retained with no data reduction, encompassing all flow key elements from the assumed set, thereby ensuring the pinnacle of information retention.

- **Buffer B1**: This buffer commences the aggregation process by omitting the flow key element with the lowest significance, the `dst_ip`, thereby retaining `protocol`, `src_port`, `dst_port`, and `src_ip`.

- **Buffer B2**: Extending the aggregation pathway, this buffer omits the next least significant flow key element, the `src_ip`, now retaining `protocol`, `src_port`, and `dst_port`.

- **Buffer B3**: Advancing further, this buffer excludes the `dst_port` flow key element, thereby retaining `protocol` and `src_port`.

- **Buffer B4**: At this zenith of data reduction, only the `protocol` flow key element is retained, marking the highest level of data reduction with the lowest degree of information retention.

Each buffer in this hierarchical structure is meticulously designed to balance the trade-off between the granularity of information and the availability of resources, orchestrating a progressive and adaptable data reduction pathway.

## Flow Handling

- **Initialization**:
    - New flows are introduced into the Main Flow Cache (`B0`).

- **Update**:
    - When a packet for an existing flow arrives, it is matched only with flows in `B0`. Flows already moved for gradual aggregation into `Buffers B1` to `B4` are not included in the update. This selective update mechanism is instrumental for contracted resources and efficient operation, as it minimizes the processing overhead. 
    
- **Movement across Buffers**:
    - When reduction is required, targeted flows (those who does not meet a certain criteria, for example have lower than a specified size of bytes) from `B0` are moved and aggregated into `B1`, and simultaneously, flows from `B1` to `B4` are also moved and aggregated to the next buffer in the sequence.
    - This movement and aggregation process is engineered to balance between information retention and resource management, ensuring an efficient operation even under resource-constrained environments.

- **Aggregation**:
  - Aggregation is the process of combining multiple flows with common flow key element attributes into a single flow record within a buffer. As flows move from one buffer to the next, their statistics are merged, including:
    - **Packet Counts**: Summed up.
    - **Flow Size (Bytes)**: Cumulated. 
    - **Flow Start:** Retained from the earliest timestamp among the aggregated flows. 
    - **Flow End:** Obtained from the latest timestamp among the aggregated flows.
    - **TCP Flags:** Omitted as they are flow-specific and would lose their informational significance upon aggregation.

  
This structured approach ensures an adaptive, resource-efficient flow measurement strategy, which is capable of providing valuable insights even under varying resource availabilities.

## References

 [1] <span id="Irino2008"></span>Hitoshi Irino, Masaru Katayama, and Shinichiro Chaki, "Study of adaptive aggregation on IPFIX," in the *Proceedings of the 2008 7th Asia-Pacific Symposium on Information and Telecommunication Technologies*, Bandos Island, Maldives, 2008, pp. 86-91. doi: `10.1109/APSITT.2008.4653545`.