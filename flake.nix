{
  description = "Workspace for experimenting with ML performance on NixOS";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    devenv.url = "github:cachix/devenv";
    devenv.inputs.nixpkgs.follows = "nixpkgs";
    nix2container.url = "github:nlewo/nix2container";
    nix2container.inputs.nixpkgs.follows = "nixpkgs";
    mk-shell-bin.url = "github:rrbutani/nix-mk-shell-bin";
    nixpkgs-python.url = "github:cachix/nixpkgs-python";
    # ml-pkgs = {
    #   inputs.nixpkgs.follows = "nixpkgs";
    #   url = "github:nixvital/ml-pkgs";
    # };
  };

  nixConfig = {
    extra-substituters = [
      "https://cuda-maintainers.cachix.org"
      "https://devenv.cachix.org"
      "https://nix-community.cachix.org"
    ];

    extra-trusted-public-keys = [
      "devenv.cachix.org-1:w1cLUi8dv3hnoSPGAuibQv+f9TZLr6cv/Hm9XgU50cw="
      "cuda-maintainers.cachix.org-1:0dq3bujKpuEPMCX6U4WylrUDZ9JyUG0VpVZa7CNfq5E="
    ];
  };

  outputs = inputs@{ flake-parts, nixpkgs, ... }:
    flake-parts.lib.mkFlake { inherit inputs; } {
      imports = [
        inputs.devenv.flakeModule
      ];
      #     flake.overlays.default = nixpkgs.lib.composeManyExtensions [
      #       inputs.ml-pkgs.overlays.torch-family
      #     ];

      systems = [ "x86_64-linux" ];

      perSystem = { config, self', inputs', pkgs, system, ... }:
        let
          ps = pkgs.python311Packages;

          jsonlines = ps.buildPythonPackage rec {
            pname = "jsonlines";
            version = "4.0.0";
            format = "setuptools";

            src = pkgs.fetchFromGitHub {
              owner = "wbolster";
              repo = pname;
              rev = version;
              hash = "sha256-KNEJdAxEgd0NGPnk9J51C3yUN2e6Cvvevth0iKOMlhE=";
            };

            propagatedBuildInputs = [
              ps.attrs
            ];

            pythonImportsCheck = [
              "jsonlines"
            ];
          };

          techqa_tools = ps.buildPythonPackage rec {
            pname = "techqa_tools";
            version = "0.0.2";
            src = pkgs.fetchgit {
              url = "https://github.com/sarahec/techqa_tools.git";
              hash = "sha256-wfuxDfHgbh04k7CjmMvoqcRStVb9XZ0a+Xbif686RoE=";
            };
            format = "pyproject";

            buildInputs = [
              ps.setuptools
              ps.wheel
            ];

            nativeBuildInputs = [
              ps.setuptools
              ps.cython_3
              ps.wheel
            ];

            propagatedBuildInputs = [
              jsonlines
              ps.orjson
              ps.spacy
            ];

            pythonImportsCheck = "techqa_tools";
          };

          spacy-en-core-web-sm = ps.buildPythonPackage rec {
            pname = "en_core_web_sm";
            version = "3.7.1";
            src = fetchTarball {
              url =
                "https://github.com/explosion/spacy-models/releases/download/${pname}-${version}/${pname}-${version}.tar.gz";
              sha256 = "sha256:10mvc8masb60zsq8mraxc032xab83v4vg23lb3ff1dwbpf67w316";
            };
            buildInputs = [ ps.spacy ];
          };
          ps_scalene = ps.buildPythonPackage rec {
            pname = "scalene";
            version = "1.5.38";
            pyproject = true;
            src = ps.fetchPypi {
              inherit pname version;
              sha256 = "sha256-LR1evkn2m6FNBmJnUUJubesxIPeHG6RDgLFBHDuxe38=";
            };

            nativeBuildInputs = [ ps.cython ps.setuptools-scm ps.pip ps.wheel ];
            propagatedBuildInputs = [ ps.cython ps.setuptools ps.wheel ps.rich ps.cloudpickle ps.pynvml ps.jinja2 ps.psutil ];
          };
          # scalene = ps.buildPythonApplication {
          #   pname = "scalene";
          #   version = "1.5.38";
          #   src = ps_scalene;
          #   buildInputs = [ ps_scalene ];
          # };
        in
        {
          # This sets `pkgs` to a nixpkgs with allowUnfree option set.
          _module.args.pkgs = import nixpkgs {
            inherit system;
            #            overlays = [ inputs.self.overlays.default ];
            config = {
              allowUnfree = true;
              allowBroken = false;
              cudaSupport = true;
            };
          };

          devenv.shells.default = {

            # imports = [
            #   # This is just like the imports in devenv.nix.
            #   # See https://devenv.sh/guides/using-with-flake-parts/#import-a-devenv-module
            #   # ./devenv-foo.nix
            # ];

            # https://devenv.sh/reference/options/
            languages.nix.enable = true;


            languages.python = {
              enable = true;
              package = (pkgs.python311.withPackages (ps: [
                ps.cupy
                ps.cython_3
                ps.ijson
                jsonlines
                ps.orjson
                ps.pip
                ps.pytest
                ps_scalene
                techqa_tools
                ps.setuptools
                ps.tqdm
                ps.spacy
                spacy-en-core-web-sm
              ])).override
                (args: { ignoreCollisions = true; }); # old cython and new cython_3 collide
              venv = {
                enable = true;
                quiet = true;
              };
            };

            # services.elasticsearch.enable = false;

            packages = with pkgs; [
              gcc
              noti
              ps_scalene
              wget
            ];

            scripts = {
              techqa_dl.exec = ''
                wget -o $PROJECT_DIR/data/TechQA.tar.gz https://huggingface.co/datasets/PrimeQA/TechQA/resolve/main/TechQA.tar.gz
                (cd $PROJECT_DIR/data
                tar -xvf TechQA.tar.gz
                cd TechQA/technote_corpus/
                bzip2 -d full_technote_collection.txt.bz2)
              '';
            };


            # NIX_LD_LIBRARY_PATH = pkgs.makeLibraryPath [
            #   pkgs.stdenv.cc.cc
            #   pkgs.zlib
            # ];
            # NIX_LD = pkgs.fileContents "${pkgs.stdenv.cc}/nix-support/dynamic-linker";
            # buildInputs = [ pkgs.python311 ];

            # enterShell = ''
            # '';
          };

        };
      flake = {
        # The usual flake attributes can be defined here, including system-
        # agnostic ones like nixosModule and system-enumerating ones, although
        # those are more easily expressed in perSystem.

      };
    };
}
