class KonachanDownloader < Formula
  include Language::Python::Virtualenv

  desc "Professional multi-threaded downloader for konachan.net"
  homepage "https://github.com/smallyunet/konachan-downloader"
  url "https://files.pythonhosted.org/packages/35/53/b966e6a62336882cf0d3d094e405626d5541610fac2e98003e11777028f0/konachan_downloader-0.0.10.tar.gz"
  sha256 "6f2f4359280c940a3fb3fa8dee7f234432418f7c206928d7e61cba035e644638"
  license "MIT"

  depends_on "python@3.11"

  def install
    virtualenv_install_with_resources
  end
end
