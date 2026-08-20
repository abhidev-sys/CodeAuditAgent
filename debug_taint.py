print("DEBUG SCRIPT STARTED")

from app.analysis.data_flow import (
    TAINT_SOURCES,
    _find_tainted_variables,
)

print("IMPORT SUCCESS")

lines = [
    '    user_id = request.args.get("id")'
]

print("TEST LINE:")
print(repr(lines[0]))

print("\nTAINT SOURCES:")
for source in TAINT_SOURCES:
    print("  ", repr(source))

print("\nCALLING FUNCTION...")

result = _find_tainted_variables(
    lines,
    8,
)

print("\nRESULT:")
print(repr(result))

print("\nRESULT TYPE:")
print(type(result))

print("\nRESULT LENGTH:")
print(len(result))