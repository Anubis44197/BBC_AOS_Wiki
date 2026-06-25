const vscode = require("vscode");
const cp = require("child_process");

function runBbc(args, cwd) {
  const terminal = vscode.window.createTerminal({ name: "BBC-AOS", cwd });
  terminal.show();
  terminal.sendText(`bbc ${args}`);
}

function activate(context) {
  const cwd = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
  const status = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 100);
  status.text = "$(zap) BBC-AOS";
  status.command = "bbc-aos.doctor";
  status.show();

  context.subscriptions.push(
    status,
    vscode.commands.registerCommand("bbc-aos.ask", async () => {
      const input = await vscode.window.showInputBox({ prompt: "BBC-AOS ask" });
      if (input) runBbc(`ask "${input.replace(/"/g, '\\"')}"`, cwd);
    }),
    vscode.commands.registerCommand("bbc-aos.index", () => runBbc("index .", cwd)),
    vscode.commands.registerCommand("bbc-aos.vaultStatus", () => runBbc("wiki status", cwd)),
    vscode.commands.registerCommand("bbc-aos.doctor", () => runBbc("doctor", cwd))
  );
}

function deactivate() {}

module.exports = { activate, deactivate };
