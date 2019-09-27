# -*- mode: python -*-

block_cipher = None

# Specify the absolute path of the project-folder (application) here:
source_path = r'C:\CoSESWeatherApp'

a = Analysis(['CoSESWeatherApp.py'],
             pathex=[source_path],
             binaries=[],
             datas=[],
             hiddenimports=['icon_rc', 'logo_rc', 'tum_logo_rc', 'header_rc', 'key_rc', 'anim_rc'],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
a.datas += [('icon.ico', source_path + '\\icon.ico','DATA'),
			('splash.png', source_path + '\\splash.png','DATA'),
			('anim_processing.gif', source_path + '\\anim_processing.gif','DATA'),
			('logo.png', source_path + '\\logo.png','DATA'),
			('key.png', source_path + '\\key.png','DATA'),
			('tum_logo.png', source_path + '\\tum_logo.png','DATA'),
			('header.png', source_path + '\\header.png','DATA'),
			('icon.png', source_path + '\\icon.png','DATA')
		   ]
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='CoSESWeatherApp_DEBUG',
          debug=True,
          strip=False,
          upx=True,
          console=True, 
		  icon=source_path + '\\icon.ico'
		  )