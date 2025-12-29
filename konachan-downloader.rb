class KonachanDownloader < Formula
  include Language::Python::Virtualenv

  desc "Professional multi-threaded downloader for konachan.net"
  homepage "https://github.com/yourusername/konachan-downloader"
  url "https://files.pythonhosted.org/packages/2c/af/5c8f5ce831bb6488ef360bcd12dc55c30024114e32253ecece0232237158/konachan_downloader-0.0.9.tar.gz"
  sha256 "7134c72184a920eaa5b312c86efa4d85ce65f48b028d06bb4e6b21d6b2f172d3"
  license "MIT"

  depends_on "python@3.11"

  def install
    virtualenv_install_with_resources
  end
end
