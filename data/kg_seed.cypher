// ── Equipment ──────────────────────────────────────────────────────────────
CREATE (:Equipment {name: 'Pump-14',   type: 'Centrifugal Pump',    location: 'Facility-A', install_year: 2018});
CREATE (:Equipment {name: 'Pump-22',   type: 'Centrifugal Pump',    location: 'Facility-B', install_year: 2020});
CREATE (:Equipment {name: 'Comp-07',   type: 'Air Compressor',      location: 'Facility-A', install_year: 2017});
CREATE (:Equipment {name: 'Motor-03',  type: 'Electric Motor',      location: 'Facility-C', install_year: 2019});
CREATE (:Equipment {name: 'Valve-09',  type: 'Control Valve',       location: 'Facility-B', install_year: 2021});

// ── Components ─────────────────────────────────────────────────────────────
CREATE (:Component {name: 'Impeller-P14',       type: 'Impeller',         part_no: 'IMP-114'});
CREATE (:Component {name: 'Bearing-P14-DE',     type: 'Drive-End Bearing',part_no: 'BRG-214-DE'});
CREATE (:Component {name: 'Bearing-P14-NDE',    type: 'NDE Bearing',      part_no: 'BRG-214-NDE'});
CREATE (:Component {name: 'Seal-P14',           type: 'Mechanical Seal',  part_no: 'SEL-314'});
CREATE (:Component {name: 'Impeller-P22',       type: 'Impeller',         part_no: 'IMP-122'});
CREATE (:Component {name: 'Bearing-C07-Main',   type: 'Main Bearing',     part_no: 'BRG-507-M'});
CREATE (:Component {name: 'Piston-C07',         type: 'Piston',           part_no: 'PST-607'});
CREATE (:Component {name: 'Stator-M03',         type: 'Stator',           part_no: 'STR-803'});
CREATE (:Component {name: 'Rotor-M03',          type: 'Rotor',            part_no: 'RTR-903'});
CREATE (:Component {name: 'Actuator-V09',       type: 'Pneumatic Actuator',part_no: 'ACT-1009'});
CREATE (:Component {name: 'Seal-V09',           type: 'Valve Seat Seal',  part_no: 'SEL-1109'});
CREATE (:Component {name: 'Coupling-P14',       type: 'Flexible Coupling', part_no: 'CPL-1214'});
CREATE (:Component {name: 'Volute-P14',         type: 'Pump Volute',       part_no: 'VLT-1314'});
CREATE (:Component {name: 'Filter-C07',         type: 'Air Intake Filter', part_no: 'FLT-1407'});
CREATE (:Component {name: 'Capacitor-M03',      type: 'Start Capacitor',   part_no: 'CAP-1503'});

// ── Fault Types ────────────────────────────────────────────────────────────
CREATE (:FaultType {name: 'Bearing Wear',         symptoms: ['excessive vibration','high temperature','noise'],            severity: 'HIGH',   fault_code: 'F-BW-01'});
CREATE (:FaultType {name: 'Impeller Cavitation',  symptoms: ['vibration','crackling noise','flow reduction','pitting'],    severity: 'MEDIUM', fault_code: 'F-CV-02'});
CREATE (:FaultType {name: 'Seal Leakage',         symptoms: ['fluid around seal face','pressure drop','vibration'],        severity: 'HIGH',   fault_code: 'F-SL-03'});
CREATE (:FaultType {name: 'Misalignment',         symptoms: ['vibration','coupling heat','axial thrust'],                  severity: 'MEDIUM', fault_code: 'F-MA-04'});
CREATE (:FaultType {name: 'Stator Winding Fault', symptoms: ['current imbalance','overheating','burning smell'],           severity: 'CRITICAL',fault_code:'F-SW-05'});
CREATE (:FaultType {name: 'Rotor Eccentricity',   symptoms: ['vibration at 2x RPM','noise','bearing overload'],            severity: 'HIGH',   fault_code: 'F-RE-06'});
CREATE (:FaultType {name: 'Piston Ring Wear',     symptoms: ['reduced pressure','blow-by','oil consumption'],              severity: 'MEDIUM', fault_code: 'F-PR-07'});
CREATE (:FaultType {name: 'Filter Fouling',       symptoms: ['reduced airflow','high inlet vacuum','temperature rise'],     severity: 'LOW',    fault_code: 'F-FF-08'});
CREATE (:FaultType {name: 'Actuator Sticking',    symptoms: ['slow valve response','control deviation','oscillation'],     severity: 'MEDIUM', fault_code: 'F-AS-09'});
CREATE (:FaultType {name: 'Valve Seat Erosion',   symptoms: ['internal leakage','pressure loss','flow noise'],             severity: 'HIGH',   fault_code: 'F-VS-10'});

// ── Maintenance Procedures ─────────────────────────────────────────────────
CREATE (:MaintenanceProcedure {name: 'Bearing Replacement',       steps: ['Isolate and lockout','Remove coupling guard','Extract bearing with puller','Inspect shaft journal','Press new bearing','Reassemble and grease','Align and test'], estimated_time: '4h',  skill_level: 'Technician'});
CREATE (:MaintenanceProcedure {name: 'NPSH Investigation',        steps: ['Check inlet pressure','Measure suction head','Inspect inlet strainer','Adjust pump speed','Verify fluid temperature'], estimated_time: '2h',  skill_level: 'Engineer'});
CREATE (:MaintenanceProcedure {name: 'Mechanical Seal Replacement',steps: ['Depressurise system','Drain casing','Remove impeller','Extract old seal','Clean seal faces','Install new seal cartridge','Pressure test'], estimated_time: '6h',  skill_level: 'Technician'});
CREATE (:MaintenanceProcedure {name: 'Laser Alignment',           steps: ['Attach alignment targets','Rotate shaft','Record offset/angularity','Adjust shims','Repeat until within 0.05mm'], estimated_time: '3h',  skill_level: 'Technician'});
CREATE (:MaintenanceProcedure {name: 'Stator Rewinding',          steps: ['Full motor disassembly','Burn out old winding','Rewind with correct gauge','Varnish and cure','Reassemble','HV insulation test'], estimated_time: '24h', skill_level: 'Specialist'});
CREATE (:MaintenanceProcedure {name: 'Rotor Balancing',           steps: ['Remove rotor','Dynamic balance on balancing machine','Correct imbalance by material removal or add-on weights','Refit and test'], estimated_time: '8h',  skill_level: 'Specialist'});
CREATE (:MaintenanceProcedure {name: 'Piston Ring Replacement',   steps: ['Depressurise compressor','Remove cylinder head','Extract piston','Replace rings','Check bore wear','Reassemble','Run-in test'], estimated_time: '6h',  skill_level: 'Technician'});
CREATE (:MaintenanceProcedure {name: 'Filter Cleaning',           steps: ['Shutdown compressor','Remove filter housing','Clean or replace element','Check housing O-ring','Reinstall','Record replacement date'], estimated_time: '1h',  skill_level: 'Operator'});
CREATE (:MaintenanceProcedure {name: 'Actuator Service',          steps: ['Isolate air supply','Remove actuator','Disassemble','Inspect diaphragm and spring','Lubricate or replace parts','Reassemble and bench-test'], estimated_time: '3h',  skill_level: 'Technician'});
CREATE (:MaintenanceProcedure {name: 'Valve Seat Reconditioning', steps: ['Remove valve from line','Lap seat with grinding compound','Check flatness with blue dye','Fit new soft seal if needed','Pressure test'], estimated_time: '5h',  skill_level: 'Technician'});

// ── Equipment → Component ──────────────────────────────────────────────────
MATCH (e:Equipment {name:'Pump-14'}),  (c:Component {name:'Impeller-P14'})       CREATE (e)-[:HAS_COMPONENT]->(c);
MATCH (e:Equipment {name:'Pump-14'}),  (c:Component {name:'Bearing-P14-DE'})     CREATE (e)-[:HAS_COMPONENT]->(c);
MATCH (e:Equipment {name:'Pump-14'}),  (c:Component {name:'Bearing-P14-NDE'})    CREATE (e)-[:HAS_COMPONENT]->(c);
MATCH (e:Equipment {name:'Pump-14'}),  (c:Component {name:'Seal-P14'})           CREATE (e)-[:HAS_COMPONENT]->(c);
MATCH (e:Equipment {name:'Pump-14'}),  (c:Component {name:'Coupling-P14'})       CREATE (e)-[:HAS_COMPONENT]->(c);
MATCH (e:Equipment {name:'Pump-14'}),  (c:Component {name:'Volute-P14'})         CREATE (e)-[:HAS_COMPONENT]->(c);
MATCH (e:Equipment {name:'Pump-22'}),  (c:Component {name:'Impeller-P22'})       CREATE (e)-[:HAS_COMPONENT]->(c);
MATCH (e:Equipment {name:'Comp-07'}),  (c:Component {name:'Bearing-C07-Main'})   CREATE (e)-[:HAS_COMPONENT]->(c);
MATCH (e:Equipment {name:'Comp-07'}),  (c:Component {name:'Piston-C07'})         CREATE (e)-[:HAS_COMPONENT]->(c);
MATCH (e:Equipment {name:'Comp-07'}),  (c:Component {name:'Filter-C07'})         CREATE (e)-[:HAS_COMPONENT]->(c);
MATCH (e:Equipment {name:'Motor-03'}), (c:Component {name:'Stator-M03'})         CREATE (e)-[:HAS_COMPONENT]->(c);
MATCH (e:Equipment {name:'Motor-03'}), (c:Component {name:'Rotor-M03'})          CREATE (e)-[:HAS_COMPONENT]->(c);
MATCH (e:Equipment {name:'Motor-03'}), (c:Component {name:'Capacitor-M03'})      CREATE (e)-[:HAS_COMPONENT]->(c);
MATCH (e:Equipment {name:'Valve-09'}), (c:Component {name:'Actuator-V09'})       CREATE (e)-[:HAS_COMPONENT]->(c);
MATCH (e:Equipment {name:'Valve-09'}), (c:Component {name:'Seal-V09'})           CREATE (e)-[:HAS_COMPONENT]->(c);

// ── Component → FaultType ──────────────────────────────────────────────────
MATCH (c:Component {name:'Bearing-P14-DE'}),  (f:FaultType {name:'Bearing Wear'})       CREATE (c)-[:CAN_EXHIBIT]->(f);
MATCH (c:Component {name:'Bearing-P14-NDE'}), (f:FaultType {name:'Bearing Wear'})       CREATE (c)-[:CAN_EXHIBIT]->(f);
MATCH (c:Component {name:'Bearing-P14-DE'}),  (f:FaultType {name:'Misalignment'})       CREATE (c)-[:CAN_EXHIBIT]->(f);
MATCH (c:Component {name:'Coupling-P14'}),     (f:FaultType {name:'Misalignment'})       CREATE (c)-[:CAN_EXHIBIT]->(f);
MATCH (c:Component {name:'Impeller-P14'}),     (f:FaultType {name:'Impeller Cavitation'})CREATE (c)-[:CAN_EXHIBIT]->(f);
MATCH (c:Component {name:'Impeller-P22'}),     (f:FaultType {name:'Impeller Cavitation'})CREATE (c)-[:CAN_EXHIBIT]->(f);
MATCH (c:Component {name:'Impeller-P14'}),     (f:FaultType {name:'Bearing Wear'})       CREATE (c)-[:CAN_EXHIBIT]->(f);
MATCH (c:Component {name:'Seal-P14'}),         (f:FaultType {name:'Seal Leakage'})       CREATE (c)-[:CAN_EXHIBIT]->(f);
MATCH (c:Component {name:'Bearing-C07-Main'}), (f:FaultType {name:'Bearing Wear'})       CREATE (c)-[:CAN_EXHIBIT]->(f);
MATCH (c:Component {name:'Piston-C07'}),       (f:FaultType {name:'Piston Ring Wear'})   CREATE (c)-[:CAN_EXHIBIT]->(f);
MATCH (c:Component {name:'Filter-C07'}),       (f:FaultType {name:'Filter Fouling'})      CREATE (c)-[:CAN_EXHIBIT]->(f);
MATCH (c:Component {name:'Stator-M03'}),       (f:FaultType {name:'Stator Winding Fault'})CREATE (c)-[:CAN_EXHIBIT]->(f);
MATCH (c:Component {name:'Rotor-M03'}),        (f:FaultType {name:'Rotor Eccentricity'}) CREATE (c)-[:CAN_EXHIBIT]->(f);
MATCH (c:Component {name:'Actuator-V09'}),     (f:FaultType {name:'Actuator Sticking'})  CREATE (c)-[:CAN_EXHIBIT]->(f);
MATCH (c:Component {name:'Seal-V09'}),         (f:FaultType {name:'Valve Seat Erosion'}) CREATE (c)-[:CAN_EXHIBIT]->(f);

// ── FaultType → MaintenanceProcedure ──────────────────────────────────────
MATCH (f:FaultType {name:'Bearing Wear'}),         (p:MaintenanceProcedure {name:'Bearing Replacement'})       CREATE (f)-[:RESOLVED_BY]->(p);
MATCH (f:FaultType {name:'Impeller Cavitation'}),  (p:MaintenanceProcedure {name:'NPSH Investigation'})        CREATE (f)-[:RESOLVED_BY]->(p);
MATCH (f:FaultType {name:'Impeller Cavitation'}),  (p:MaintenanceProcedure {name:'Bearing Replacement'})       CREATE (f)-[:RESOLVED_BY]->(p);
MATCH (f:FaultType {name:'Seal Leakage'}),         (p:MaintenanceProcedure {name:'Mechanical Seal Replacement'})CREATE (f)-[:RESOLVED_BY]->(p);
MATCH (f:FaultType {name:'Misalignment'}),         (p:MaintenanceProcedure {name:'Laser Alignment'})           CREATE (f)-[:RESOLVED_BY]->(p);
MATCH (f:FaultType {name:'Stator Winding Fault'}), (p:MaintenanceProcedure {name:'Stator Rewinding'})          CREATE (f)-[:RESOLVED_BY]->(p);
MATCH (f:FaultType {name:'Rotor Eccentricity'}),   (p:MaintenanceProcedure {name:'Rotor Balancing'})           CREATE (f)-[:RESOLVED_BY]->(p);
MATCH (f:FaultType {name:'Piston Ring Wear'}),     (p:MaintenanceProcedure {name:'Piston Ring Replacement'})   CREATE (f)-[:RESOLVED_BY]->(p);
MATCH (f:FaultType {name:'Filter Fouling'}),       (p:MaintenanceProcedure {name:'Filter Cleaning'})           CREATE (f)-[:RESOLVED_BY]->(p);
MATCH (f:FaultType {name:'Actuator Sticking'}),    (p:MaintenanceProcedure {name:'Actuator Service'})          CREATE (f)-[:RESOLVED_BY]->(p);
MATCH (f:FaultType {name:'Valve Seat Erosion'}),   (p:MaintenanceProcedure {name:'Valve Seat Reconditioning'}) CREATE (f)-[:RESOLVED_BY]->(p)
