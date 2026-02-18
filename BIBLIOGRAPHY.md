# Bibliography & Standards References

## IEC Standards

- **IEC 61968-9:2024 Ed 3.0** - Application Integration at Electric Utilities – System Interfaces for Distribution Management – Part 9: Interfaces for Meter Reading and Control. International Electrotechnical Commission. Defines CIM EndDevice, MeterReading, ReadingType, IntervalBlock, and UsagePoint models used throughout this implementation.

- **IEC 61968-100:2022** - Application Integration at Electric Utilities – System Interfaces for Distribution Management – Part 100: Implementation Profiles. IEC. Defines message exchange patterns and RESTful interface profiles for CIM-based systems.

- **IEC 61970-301:2020** - Energy Management System Application Program Interface (EMS-API) – Part 301: Common Information Model (CIM) Base. IEC. Defines core CIM packages including IdentifiedObject (mRID), UnitSymbol, PhaseCode, and DateTimeInterval.

- **IEC 61970-501:2006** - Energy Management System Application Program Interface (EMS-API) – Part 501: Common Information Model Resource Description Framework (CIM RDF) Schema. IEC. Defines the RDF representation of CIM.

- **IEC 61970-552:2016** - Energy Management System Application Program Interface (EMS-API) – Part 552: CIM XML Model Exchange Format. IEC. Defines XML serialization of CIM models.

## Open Source CIM Resources

- **CIMug Standards Artifacts** - CIM Users Group. Available at: https://cimug.org/cimdocs/standards-artifacts/ — Provides access to CIM UML models, profiles, and related standards documentation.

- **TC57CIM Python Reference Implementation** - pjm4github. Available at: https://github.com/pjm4github/TC57CIM — Python translation of TC57 CIM UML classes. Referenced for class structures: EndDevice, Meter, ComModule, ReadingType, IntervalReading, IntervalBlock, MeterReading, UsagePoint, FlowDirectionKind, CommodityKind, MeasurementKind, AccumulationKind, ReadingQualityType, UsagePointConnectedKind.

- **CIMug GitHub Organization** - CIM Users Group. Available at: https://github.com/CIMug-org — Hosts CIM-related tools, profiles, and community resources.

- **CIM Modeling Guide** - UCAIug. Available at: https://cim-mg.ucaiug.io/latest/ — Official CIM modeling guidelines and best practices.

- **CIMTool** - UCAIug. Available at: https://cimtool.ucaiug.io/ — Open-source tool for working with CIM profiles and schemas.

- **CIMug Artifacts Repository** - CIM Users Group. Available at: https://github.com/cimug-org/artifacts — Additional CIM artifacts including sample models and validation tools.

- **CIM University Presentations** - CIM Users Group. IEC 61968-9 focused sessions at Oslo 2014 and Dallas 2018 CIM University events.

## Landis+Gyr Public Documentation

- **E350 Residential Meter** - Landis+Gyr. Product brochure and datasheet. Single-phase residential meter with RF Mesh/PLC communication. Specifications: Form 2S, 200A class, 120-480V.

- **E360 Residential Meter** - Landis+Gyr. LTE Technical Data sheets for 1-phase and 3-phase configurations. Advanced residential meter with cellular LTE communication. Specifications: Form 2S, 200A class, 120-480V.

- **E650 S4x Commercial & Industrial Meter** - Landis+Gyr. Product specifications and user manual. Polyphase C&I meter with advanced demand measurement. Specifications: Form 9S/16S, 400A class, 120-480V, CT-rated.

- **E660/Revelo IoT Grid Sensing Platform** - Landis+Gyr. Platform specification. Advanced grid-edge sensing with IoT capabilities. Specifications: Form 16S, 800A class, cellular LTE communication.

- **Gridstream Head-End System (HES)** - Landis+Gyr. Product description. Central data collection system for AMI field devices. Manages meter communication, data collection, and firmware management.

- **Core MDMS (Meter Data Management System)** - Landis+Gyr. Product documentation. Meter data management with Validation, Estimation, and Editing (VEE) pipeline. Processes raw meter data into billing-quality reads.

- **Gridstream Analytics** - Landis+Gyr. Solution overview. Analytics platform for demand analysis, voltage monitoring, power quality, and revenue protection.

- **AMI Communication Pathway Selection Guide** - Landis+Gyr. Technical guide covering RF Mesh, PLC, and Cellular LTE communication options for AMI deployments.

- **IDIS White Paper** - Landis+Gyr. Interoperable Device Interface Specifications for multi-vendor AMI interoperability.

- **AMM Data Security White Paper** - Landis+Gyr. Advanced Metering Management data security architecture and practices.

## Industry Standards

- **ANSI C84.1-2020** - Electric Power Systems and Equipment – Voltage Ratings (60 Hz). American National Standards Institute. Defines Range A (normal) and Range B (emergency) service voltage limits. Range A for 120V nominal: 114V-126V (±5%).

- **ANSI C12.18-2006** - Protocol Specification for ANSI Type 2 Optical Port. ANSI. Meter communication protocol for optical ports.

- **ANSI C12.20-2015** - Electricity Meters – 0.2 and 0.5 Accuracy Classes. ANSI. Revenue metering accuracy standards.

- **DLMS/COSEM (IEC 62056)** - Device Language Message Specification / Companion Specification for Energy Metering. DLMS User Association. Standardized meter data exchange protocol suite.

- **Green Button / NAESB REQ.21 ESPI** - North American Energy Standards Board. Energy Services Provider Interface standard for consumer energy data access (Green Button).

- **IEEE 2030.5-2018** - IEEE Standard for Smart Energy Profile Application Protocol (SEP 2.0). IEEE. Application-layer protocol for smart energy devices.

## Academic & Technical Reports

- **PNNL-34946** - *Power Application Developer's Guide to CIM*. Pacific Northwest National Laboratory. Comprehensive developer guide covering CIM data models, ReadingType structure, and implementation patterns.

- **PNNL-32679** - *Enabling Data Exchange with CIM*. Pacific Northwest National Laboratory. Guide for implementing CIM-based data exchange in utility systems.

- **CIM Primer Seventh Edition (EPRI 3002021840)** - *Common Information Model Primer*. Electric Power Research Institute. Introduction to CIM concepts, mRID usage, naming conventions, and model relationships.

- **KTH "CIM for Dummies"** - Royal Institute of Technology, Stockholm. *Introduction to IEC 61970-301 & IEC 61968-11*. Accessible introduction to CIM core and distribution domain models.

---

*Note: IEC standards are available for purchase from the IEC webstore (https://webstore.iec.ch/). Landis+Gyr product documentation is publicly available on the Landis+Gyr website. Open-source resources are freely available at the URLs listed above.*
