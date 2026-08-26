----------------------------- MODULE CertFusion -----------------------------
EXTENDS Naturals, FiniteSets

CONSTANTS Inputs, Properties, Classes, NULL

VARIABLES phase, input, encoded, abstracted, property,
          solverResult, certificate, predSet, outputStatus

Phases == {"Init", "Loaded", "Encoded", "Abstracted", "PropertyReady",
           "SMTChecked", "Certified", "Counterexample", "Timeout",
           "ConformalReady", "Released"}

SolverResults == {"UNSAT", "SAT", "TIMEOUT", "NONE"}
OutputStatus == {"CERTIFIED", "UNCERTIFIED", "BLOCKED"}

Init ==
  /\ phase = "Init"
  /\ input = NULL
  /\ encoded = FALSE
  /\ abstracted = FALSE
  /\ property = NULL
  /\ solverResult = "NONE"
  /\ certificate = FALSE
  /\ predSet = {}
  /\ outputStatus = "BLOCKED"

LoadInput ==
  /\ phase = "Init"
  /\ input' \in Inputs
  /\ phase' = "Loaded"
  /\ UNCHANGED <<encoded, abstracted, property,
                 solverResult, certificate, predSet, outputStatus>>

EncodeInput ==
  /\ phase = "Loaded"
  /\ encoded' = TRUE
  /\ phase' = "Encoded"
  /\ UNCHANGED <<input, abstracted, property,
                 solverResult, certificate, predSet, outputStatus>>

AbstractLatentSpace ==
  /\ phase = "Encoded"
  /\ encoded = TRUE
  /\ abstracted' = TRUE
  /\ phase' = "Abstracted"
  /\ UNCHANGED <<input, encoded, property,
                 solverResult, certificate, predSet, outputStatus>>

GenerateProperty ==
  /\ phase = "Abstracted"
  /\ abstracted = TRUE
  /\ property' \in Properties
  /\ phase' = "PropertyReady"
  /\ UNCHANGED <<input, encoded, abstracted,
                 solverResult, certificate, predSet, outputStatus>>

RunSMT ==
  /\ phase = "PropertyReady"
  /\ solverResult' \in {"UNSAT", "SAT", "TIMEOUT"}
  /\ phase' = "SMTChecked"
  /\ UNCHANGED <<input, encoded, abstracted,
                 property, certificate, predSet, outputStatus>>

IssueCertificate ==
  /\ phase = "SMTChecked"
  /\ solverResult = "UNSAT"
  /\ certificate' = TRUE
  /\ phase' = "Certified"
  /\ UNCHANGED <<input, encoded, abstracted,
                 property, solverResult, predSet, outputStatus>>

RecordCounterexample ==
  /\ phase = "SMTChecked"
  /\ solverResult = "SAT"
  /\ certificate' = FALSE
  /\ phase' = "Counterexample"
  /\ UNCHANGED <<input, encoded, abstracted,
                 property, solverResult, predSet, outputStatus>>

HandleTimeout ==
  /\ phase = "SMTChecked"
  /\ solverResult = "TIMEOUT"
  /\ certificate' = FALSE
  /\ phase' = "Timeout"
  /\ UNCHANGED <<input, encoded, abstracted,
                 property, solverResult, predSet, outputStatus>>

GenerateConformalSet ==
  /\ phase \in {"Certified", "Counterexample", "Timeout"}
  /\ predSet' \subseteq Classes
  /\ predSet' # {}
  /\ phase' = "ConformalReady"
  /\ UNCHANGED <<input, encoded, abstracted,
                 property, solverResult, certificate, outputStatus>>

ReleaseOutput ==
  /\ phase = "ConformalReady"
  /\ IF certificate = TRUE
        THEN outputStatus' = "CERTIFIED"
        ELSE outputStatus' = "UNCERTIFIED"
  /\ phase' = "Released"
  /\ UNCHANGED <<input, encoded, abstracted,
                 property, solverResult, certificate, predSet>>

Next == LoadInput \/ EncodeInput \/ AbstractLatentSpace \/ GenerateProperty
        \/ RunSMT \/ IssueCertificate \/ RecordCounterexample
        \/ HandleTimeout \/ GenerateConformalSet \/ ReleaseOutput

Spec == Init /\ [][Next]_<<phase, input, encoded, abstracted, property,
                         solverResult, certificate, predSet, outputStatus>>

TypeOK ==
  /\ phase \in Phases
  /\ solverResult \in SolverResults
  /\ outputStatus \in OutputStatus
  /\ certificate \in BOOLEAN
  /\ encoded \in BOOLEAN
  /\ abstracted \in BOOLEAN
  /\ predSet \subseteq Classes

NoUnsafeRelease ==
  /\ phase = "Released"
  /\ outputStatus = "CERTIFIED"
  => certificate = TRUE /\ solverResult = "UNSAT"

TimeoutNotCertified == solverResult = "TIMEOUT" => certificate = FALSE
CounterexampleNotCertified == solverResult = "SAT" => certificate = FALSE
ConformalBeforeRelease == phase = "Released" => predSet # {}
TraceableRelease == phase = "Released" => input # NULL /\ property # NULL
=============================================================================