# KV to SIRI-SX

Build a small, modular command-line application that converts BISON KV17 and
BISON KV7/KV8 messages into SIRI-SX messages using a user-editable TOML
mapping file.

## Goals

- Provide a basic, understandable mapping from KV17 and KV7/KV8 fields to
  their SIRI-SX equivalents.
- Support direct field mappings without requiring custom code.
- Support simple field transformations, including:
  - splitting one source field into multiple target fields;
  - removing or ignoring a source field;
  - changing a field's type or format; and
  - composing a target field from one or more source fields when practical.
- Keep the application modular, dependency-light, and easy to extend.
- Prefer predictable behavior and clear errors over implicit or clever logic.

## Mapping Configuration

Provide the checked-in example [mapping.toml](mapping.toml), based on the
released BISON KV15, KV7/8, and KV17 schemas and the SIRI v2.3 XSDs. It should
demonstrate both message families and the supported operations. The
configuration should make the following explicit:

- source message type and field;
- target SIRI-SX message type and field;
- operation or transformation to apply; and
- behavior for missing, empty, or invalid values.

Pin the source and target schema versions in comments or project metadata.
Treat paths in the example as XML element paths relative to the message or
SIRI-SX situation element, and keep XML namespace and wrapper construction in
the converter rather than duplicating it in every mapping rule.

Keep the mapping engine independent from the CLI and from individual message
formats so additional mappings can be added without changing the conversion
pipeline.

## Command-Line Interface

The converter must accept KV messages from either:

- a file supplied as a command-line argument; or
- standard input, so it can be used in a pipeline.

Define a minimal CLI with clear help text. It should support selecting the
mapping configuration and writing converted SIRI-SX messages to standard
output. Errors must identify the relevant input message, field, and mapping
rule when possible, and must use a non-zero exit status on failure.

## Scope and Non-Goals

- Implement only the mapping and transformation features needed for the
  example configuration.
- Do not build a general-purpose expression language.
- Do not hide unsupported fields or transformations; report them clearly.
- Avoid premature abstractions, broad schema generation, and unrelated
	infrastructure.

## Acceptance Criteria

- A KV17 message can be converted using at least one direct mapping and one
	transformation from `mapping.toml`.
- A KV7/KV8 message can be converted using at least one direct mapping.
- The same conversion works when the message is read from a file or stdin.
- Missing and invalid values produce deterministic, actionable errors.
- The mapping engine can be tested independently of command-line I/O.
- The repository includes a short usage example and focused tests for direct
	mapping, splitting, removal, type conversion, stdin input, and file input.