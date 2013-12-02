import coverage
from nose.plugins.cover import Coverage as VerboseCoverage


class Coverage(VerboseCoverage):
    __doc__ = VerboseCoverage.__doc__ + """
    Subclass of nose.plugin.cover.Coverage that add option to omit pathes from coverage output."""

    omit_path = []

    def options(self, parser, env):
        """
        Add options to command line.
        """
        super(Coverage, self).options(parser, env)
        parser.add_option("--cover-omit", action="append",
                          default=env.get('NOSE_COVER_OMIT'),
                          metavar="PATH",
                          dest="omit_path",
                          help="Omit [NOSE_COVER_OMIT] from coverage output.")

    def configure(self, options, conf):
        """
        Configure plugin.
        """
        super(Coverage, self).configure(options, conf)
        self.omit_path = options.omit_path

        if self.enabled:
            self.status['active'] = True
            self.coverInstance = coverage.coverage(
                auto_data=False,
                branch=self.coverBranches,
                data_suffix=None,
                omit=self.omit_path)
