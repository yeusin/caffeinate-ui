a = Analysis(
    ["caffeinate_ui.py"],
    datas=[("assets", "assets")],
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Caffeinate UI",
    console=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    name="Caffeinate UI",
)

app = BUNDLE(
    coll,
    name="Caffeinate UI.app",
    icon="assets/app.icns",
    bundle_identifier="com.caffeinate-ui.app",
    info_plist={
        "LSUIElement": True,
    },
)
