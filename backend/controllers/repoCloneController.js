const simpleGit = require("simple-git")
const path = require("path");
const fs = require("fs")

const cloneRepo = (async(req, res) => {

    try {
        const repoUrl = req.body.repoUrl;

        const folderName = path.join(
            __dirname,
            "../repos"
        )

        if (!fs.existsSync(folderName)) {
            fs.mkdirSync(folderName)
        }

        await simpleGit().clone(
            repoUrl,
            folderName
        );

        return res.json({
            message:"Repository cloned Successfully"
        })

    } catch (error) {

        console.log(error)
    }
})

module.exports={
    cloneRepo
}