{ pkgs ? import <nixpkgs> {} }:

let
  # Sadece PySide6 içeren Python ortamımız
  pythonEnv = pkgs.python3.withPackages (ps: with ps; [
    pyside6
  ]);
in
pkgs.mkShell {
  packages = with pkgs; [
    pythonEnv

    # Wayland üzerinde çalışıyorsan Qt uygulamalarının düzgün çalışması için
    qt6.qtwayland
  ];

  # Qt'nin eklentileri (platform temaları vb.) doğru bulabilmesi için ortam değişkeni
  QT_PLUGIN_PATH = "${pkgs.qt6.qtbase}/${pkgs.qt6.qtbase.qtPluginPrefix}";

  shellHook = ''
    echo "==================================================="
    echo "🚀 Qt GUI Geliştirme Ortamı Hazır!"
    echo "🐍 $(python --version)"
    echo "🔍 Sistemdeki araç kullanılacak: $(which protonvpn || echo 'Bulunamadı!')"
    echo "==================================================="

    # Wayland üzerinde çalışıyorsa Qt'yi Wayland'i kullanmaya zorla
    if [ "$XDG_SESSION_TYPE" = "wayland" ]; then
      export QT_QPA_PLATFORM="wayland;xcb"
    fi
  '';
}
