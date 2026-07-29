const express=require("express");
const router=express.Router()
const repo_dataController=require("../controllers/repo_dataController")
const PR_Controller=require("../controllers/PullRequestsController")
const repo_cloneController=require("../controllers/repoCloneController")


router.route("/repos")
    .get(repo_dataController.fetchRepoData)

router.route("/cloneRepo")
    .post(repo_cloneController.cloneRepo)


router.route("/PullRequests")
    .get(PR_Controller.fetch_Pull_Requests)

module.exports=router;