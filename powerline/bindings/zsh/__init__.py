# vim:fileencoding=utf-8:noet
import zsh
import atexit
from powerline.shell import ShellPowerline
from powerline.lib import parsedotval


used_powerlines = []


def shutdown():
	for powerline in used_powerlines:
		powerline.shutdown()


def get_var_config(var):
	try:
		return [parsedotval(i) for i in zsh.getvalue(var).items()]
	except:
		return None


class Args(object):
	ext = ['shell']
	renderer_module = 'zsh_prompt'

	@property
	def last_exit_code(self):
		return zsh.last_exit_code()

	@property
	def last_pipe_status(self):
		return zsh.pipestatus()

	@property
	def config(self):
		try:
			return get_var_config('POWERLINE_CONFIG')
		except IndexError:
			return None

	@property
	def theme_option(self):
		try:
			return get_var_config('POWERLINE_THEME_CONFIG')
		except IndexError:
			return None

	@property
	def config_path(self):
		try:
			return zsh.getvalue('POWERLINE_CONFIG_PATH')
		except IndexError:
			return None

	@property
	def jobnum(self):
		zsh.eval('integer _POWERLINE_JOBNUM=${(%):-%j}')
		return zsh.getvalue('_POWERLINE_JOBNUM')


def string(s):
	if type(s) is bytes:
		return s.decode('utf-8', 'replace')
	else:
		return str(s)


class Environment(object):
	@staticmethod
	def __getitem__(key):
		try:
			return string(zsh.getvalue(key))
		except IndexError as e:
			raise KeyError(*e.args)

	@staticmethod
	def get(key, default=None):
		try:
			return string(zsh.getvalue(key))
		except IndexError:
			return default

	@staticmethod
	def __contains__(key):
		try:
			zsh.getvalue(key)
			return True
		except IndexError:
			return False


environ = Environment()


class Prompt(object):
	__slots__ = ('powerline', 'side', 'savedpsvar', 'savedps', 'args', 'theme')

	def __init__(self, powerline, side, theme, savedpsvar=None, savedps=None):
		self.powerline = powerline
		self.side = side
		self.savedpsvar = savedpsvar
		self.savedps = savedps
		self.args = powerline.args
		self.theme = theme

	def __str__(self):
		zsh.eval('_POWERLINE_PARSER_STATE="${(%):-%_}"')
		segment_info = {
			'args': self.args,
			'environ': environ,
			'client_id': 1,
			'local_theme': self.theme,
			'parser_state': zsh.getvalue('_POWERLINE_PARSER_STATE'),
		}
		r = self.powerline.render(
			width=zsh.columns(),
			side=self.side,
			segment_info=segment_info,
		)
		if type(r) is not str:
			if type(r) is bytes:
				return r.decode('utf-8')
			else:
				return r.encode('utf-8')
		return r

	def __del__(self):
		if self.savedps:
			zsh.setvalue(self.savedpsvar, self.savedps)
		used_powerlines.remove(self.powerline)
		if self.powerline not in used_powerlines:
			self.powerline.shutdown()


def set_prompt(powerline, psvar, side, theme):
	try:
		savedps = zsh.getvalue(psvar)
	except IndexError:
		savedps = None
	zpyvar = 'ZPYTHON_POWERLINE_' + psvar
	prompt = Prompt(powerline, side, theme, psvar, savedps)
	zsh.set_special_string(zpyvar, prompt)
	zsh.setvalue(psvar, '${' + zpyvar + '}')


def setup():
	powerline = ShellPowerline(Args())
	used_powerlines.append(powerline)
	used_powerlines.append(powerline)
	set_prompt(powerline, 'PS1', 'left', None)
	set_prompt(powerline, 'RPS1', 'right', None)
	set_prompt(powerline, 'PS2', 'left', 'continuation')
	set_prompt(powerline, 'RPS2', 'right', 'continuation')
	set_prompt(powerline, 'PS3', 'left', 'select')
	atexit.register(shutdown)
