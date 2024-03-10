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
    ml-pkgs = {
      inputs.nixpkgs.follows = "nixpkgs";
      url = "github:nixvital/ml-pkgs";
    };
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

          techqa_tools = ps.buildPythonPackage rec {
            pname = "techqa_tools";
            version = "unstable 3-10-24";
            src = pkgs.fetchgit {
              url = "https://github.com/sarahec/spacy-test.git";
              sparseCheckout = [ "lib/techqa_tools" ];
              hash = "sha256-k43LfXmqXiLXmy4o049N1cwHB1eOJRfHdHTCjhFJTDA=";
            };
            format = "pyproject";

            prePatch = ''
              cd lib/techqa_tools
            '';

            buildInputs = [ ps.setuptools ps.wheel ps.cython_3 ];

            propagatedBuildInputs = [
              ps.jsonlines
              ps.orjson
              ps.spacy
            ];
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
          scalene = ps.buildPythonPackage rec {
            pname = "scalene";
            version = "1.5.36";
            pyproject = true;
            src = ps.fetchPypi {
              inherit pname version;
              sha256 = "sha256-yKRXbSyywb71ma39JeD5DJgdUKwnJDyi1hZA+im9S8Y=";
            };

            nativeBuildInputs = [ ps.cython ps.setuptools-scm ps.pip ps.wheel ];
            propagatedBuildInputs = [ ps.cython ps.setuptools ps.wheel ps.rich ps.cloudpickle ps.pynvml ps.jinja2 ps.psutil ];
          };
        in
        {
          # This sets `pkgs` to a nixpkgs with allowUnfree option set.
          _module.args.pkgs = import nixpkgs {
            inherit system;
            #            overlays = [ inputs.self.overlays.default ];
            config = {
              allowUnfree = true;
              allowBroken = false;
              cudaSupport = false;
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
                # ps.cupy
                techqa_tools
                ps.cython_3
                ps.ijson
                ps.pip
                ps.pytest
                scalene
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

            services.elasticsearch.enable = true;

            packages = with pkgs; [
              gcc
              noti
              scalene
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

            enterShell = ''
              export PROJECT_DIR=$DEVENV_ROOT
            '';
          };

        };
      flake = {
        # The usual flake attributes can be defined here, including system-
        # agnostic ones like nixosModule and system-enumerating ones, although
        # those are more easily expressed in perSystem.

      };
    };
}
