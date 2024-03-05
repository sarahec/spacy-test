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
            version = "1.5.35";
            pyproject = true;
            src = ps.fetchPypi {
              inherit pname version;
              sha256 = "3s0KN06RivCN4G5/LZf+r7GtAlKwqRuZwUtrY2T2Bew=";
            };

            nativeBuildInputs = [ ps.cython ps.setuptools-scm ps.pip ps.wheel ];
            propagatedBuildInputs = [ ps.cython ps.setuptools ps.wheel ps.rich ps.cloudpickle ps.pynvml ps.jinja2 ps.psutil ];

            postPatch = ''
              substituteInPlace setup.py \
                --replace-warn "pynvml>=11.0.0,<11.5" "pynvml~=11.5.0"
              substituteInPlace requirements.txt \
                --replace-warn "pynvml~=11.0.0" "pynvml~=11.5.0"
            '';
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
                ps.cython_3
                ps.ijson
                ps.jsonlines
                ps.orjson
                ps.pip
                ps.pytest
                scalene
                ps.setuptools
                ps.tqdm
                ps.spacy
                spacy-en-core-web-sm
              ])).override
                (args: { ignoreCollisions = true; }); # old cython and new cython_3 collide
              venv = {
                enable = true;
                quiet = true;
                requirements = ''
                  austin-dist
                '';
              };
            };

            services.elasticsearch.enable = true;

            packages = with pkgs; [
              noti
              scalene
              wget
            ];

            scripts = {
              wikipedia_dl.exec = ''
                wget https://nlp.stanford.edu/projects/hotpotqa/enwiki-20171001-pages-meta-current-withlinks-processed.tar.bz2
                wget https://dumps.wikimedia.org/enwiki/latest/enwiki-latest-page_props.sql.gz
                tar -xvf enwiki-20171001-pages-meta-current-withlinks-processed.tar.bz2
                mkdir -p $PROJECT_DIR/data/wikipedia/enwiki_whole
                mv enwiki-20171001-pages-meta-current-withlinks-processed/* $PROJECT_DIR/data/wikipedia/enwiki_whole/
                gzip -d enwiki-latest-page_props.sql.gz
                mkdir -p $PROJECT_DIR/data/wikipedia/enwiki_props
                mv enwiki-latest-page_props.sql $PROJECT_DIR/data/wikipedia/enwiki_props/
              '';

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
