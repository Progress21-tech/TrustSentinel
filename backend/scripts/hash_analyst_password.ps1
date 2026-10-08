$secure = Read-Host "Enter analyst password (at least 12 characters)" -AsSecureString
$confirmation = Read-Host "Confirm analyst password" -AsSecureString
$pointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
$confirmationPointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($confirmation)

try {
    $password = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($pointer)
    $confirmedPassword = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($confirmationPointer)
    if ($password.Length -lt 12) {
        throw "Password must be at least 12 characters."
    }
    if ($password -cne $confirmedPassword) {
        throw "Passwords do not match. Run the command again."
    }

    $source = @'
using System;
using System.Security.Cryptography;
using System.Text;

public static class TrustSentinelPasswordHash
{
    private const int Iterations = 310000;

    public static string Create(string password)
    {
        byte[] salt = new byte[16];
        using (RandomNumberGenerator random = RandomNumberGenerator.Create())
        {
            random.GetBytes(salt);
        }

        byte[] block = new byte[20];
        Buffer.BlockCopy(salt, 0, block, 0, salt.Length);
        block[19] = 1;

        byte[] derived;
        using (HMACSHA256 hmac = new HMACSHA256(Encoding.UTF8.GetBytes(password)))
        {
            byte[] u = hmac.ComputeHash(block);
            derived = (byte[])u.Clone();
            for (int round = 2; round <= Iterations; round++)
            {
                u = hmac.ComputeHash(u);
                for (int index = 0; index < derived.Length; index++)
                {
                    derived[index] ^= u[index];
                }
            }
        }

        return "pbkdf2_sha256$" + Iterations + "$" + Encode(salt) + "$" + Encode(derived);
    }

    private static string Encode(byte[] value)
    {
        return Convert.ToBase64String(value).TrimEnd('=').Replace('+', '-').Replace('/', '_');
    }
}
'@

    Add-Type -TypeDefinition $source -Language CSharp
    [TrustSentinelPasswordHash]::Create($password)
} finally {
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($pointer)
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($confirmationPointer)
    $secure.Dispose()
    $confirmation.Dispose()
}
